const { Plugin, Notice } = require('obsidian');
const { spawn } = require('child_process');
const path = require('path');

module.exports = class FactorySyncPlugin extends Plugin {
    async onload() {
        console.log('[FactorySync] Plugin loaded with Live-Sync support.');
        
        let renameDebounceTimer = null;
        let previewDebounceTimer = null;
        
        const factoryRoot = path.resolve(this.app.vault.adapter.basePath, '..');
        const renameScript = path.join(factoryRoot, '.agents', 'scripts', 'safe_rename.py');
        const previewScript = path.join(factoryRoot, '.agents', 'scripts', 'generate_coverage_preview.py');

        const isAtomFile = (filePath) => {
            if (!filePath) return false;
            // Chống Infinite Loop: Bỏ qua chính file preview và cấu hình nội bộ
            if (filePath.includes('audience-knowledge-coverage-preview') || filePath.startsWith('.obsidian')) {
                return false;
            }
            return filePath.startsWith('01-Atomic') || 
                   filePath.startsWith('02-sources') || 
                   filePath.includes('personas') || 
                   filePath.includes('production-log.md');
        };

        const triggerPreviewRefresh = () => {
            clearTimeout(previewDebounceTimer);
            previewDebounceTimer = setTimeout(() => {
                const proc = spawn('python', [previewScript, '--factory-root', factoryRoot], {
                    cwd: factoryRoot,
                    windowsHide: true
                });
                proc.on('close', (code) => {
                    if (code === 0) {
                        console.log('[FactorySync] Preview Table refreshed.');
                    }
                });
            }, 1500); // 1.5s Debounce
        };

        // 1. Tự động quét 1 lần ngay khi khởi động Obsidian (Startup Hook)
        this.app.workspace.onLayoutReady(() => {
            triggerPreviewRefresh();
        });

        // 2. Lắng nghe sự kiện Đổi tên (Rename)
        this.registerEvent(
            this.app.vault.on('rename', (file, oldPath) => {
                if (!file.path.endsWith('.md')) return;
                const oldBase = path.basename(oldPath, '.md');
                const newBase = path.basename(file.path, '.md');
                if (oldBase === newBase) return;

                clearTimeout(renameDebounceTimer);
                renameDebounceTimer = setTimeout(() => {
                    const args = [renameScript, '--old-name', oldBase, '--new-name', newBase, '--sync-only', '--scan-root', factoryRoot];
                    const proc = spawn('python', args, { cwd: factoryRoot, windowsHide: true });
                    let stdout = '';
                    proc.stdout.on('data', (d) => stdout += d.toString());
                    proc.on('close', (code) => {
                        if (code === 0) {
                            try {
                                const res = JSON.parse(stdout);
                                new Notice(`[Factory Sync] 🔄 Đã đồng bộ ${res.total_files_updated} file trong Content Factory`, 4000);
                            } catch (e) {
                                new Notice(`[Factory Sync] 🔄 Đã đồng bộ tham chiếu file thành công!`, 4000);
                            }
                            triggerPreviewRefresh();
                        }
                    });
                }, 300);
            })
        );

        // 3. Lắng nghe sự kiện Chỉnh sửa (Modify)
        this.registerEvent(
            this.app.vault.on('modify', (file) => {
                if (isAtomFile(file.path)) {
                    triggerPreviewRefresh();
                }
            })
        );

        // 4. Lắng nghe sự kiện Tạo mới (Create)
        this.registerEvent(
            this.app.vault.on('create', (file) => {
                if (isAtomFile(file.path)) {
                    triggerPreviewRefresh();
                }
            })
        );

        // 5. Lắng nghe sự kiện Xóa (Delete)
        this.registerEvent(
            this.app.vault.on('delete', (file) => {
                if (isAtomFile(file.path)) {
                    triggerPreviewRefresh();
                }
            })
        );
    }

    onunload() {
        console.log('[FactorySync] Plugin unloaded.');
    }
};
