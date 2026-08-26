/**
 * factory-sync - main.js
 * Last update: 18/08/2026 22:50 (GMT+7)
 * Vai tro: Obsidian plugin quan ly dong bo du lieu theo thoi gian thuc (Live-Sync) va Safe-Rename.
 * Su dung khi: Chay tu dong trong Obsidian khi vault duoc mo.
 * Output: Tu dong cap nhat tham chieu khi doi ten file va goi generate_coverage_preview.py cap nhat ma tran phu tri thuc.
 * Tom tat logic hoat dong:
 *   1. Startup Hook: Tu dong goi preview script 1 lan khi khoi dong.
 *   2. Vault Events: Bat su kien rename (goi safe_rename.py), create/modify/delete (goi preview refresh).
 *   3. External Watcher: Su dung fs.watch theo doi thu muc personas/ de tu dong refresh khi sua topic_map.yaml tu ben ngoai.
 *   4. Memory Management: Tu dong giai phong watcher khi unload plugin.
 */

const { Plugin, Notice } = require('obsidian');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

module.exports = class FactorySyncPlugin extends Plugin {
    async onload() {
        console.log('[FactorySync] Plugin loaded with Live-Sync & Persona Watcher support.');
        
        let renameDebounceTimer = null;
        let previewDebounceTimer = null;
        this.personasWatcher = null;
        
        const factoryRoot = path.resolve(this.app.vault.adapter.basePath, '..');
        const renameScript = path.join(factoryRoot, '.agents', 'scripts', 'safe_rename.py');
        const previewScript = path.join(factoryRoot, '.agents', 'scripts', 'generate_coverage_preview.py');
        const personasDir = path.join(factoryRoot, 'personas');

        // Bo loc kiem tra file thuoc pham vi can theo doi trong Vault
        const isAtomFile = (filePath) => {
            if (!filePath) return false;
            // Chống Infinite Loop: Bỏ qua các file báo cáo tự động và cấu hình nội bộ
            if (filePath.includes('audience-knowledge-coverage-preview') || 
                filePath.includes('vault-health-report') || 
                filePath.includes('audience-hierarchy') || 
                filePath.startsWith('.obsidian')) {
                return false;
            }
            return filePath.startsWith('01-Atomic') || 
                   filePath.startsWith('02-sources') || 
                   filePath.includes('personas') || 
                   filePath.includes('production-log.md');
        };

        // Ham kich hoat cap nhat Preview Table voi bo dem debounce 1.5 giay
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

        // 2. Theo dõi thư mục personas/ từ bên ngoài Vault (External fs.watch)
        if (fs.existsSync(personasDir)) {
            try {
                this.personasWatcher = fs.watch(personasDir, { recursive: true }, (eventType, filename) => {
                    if (filename && (filename.endsWith('.yaml') || filename.endsWith('.yml') || filename.endsWith('.json'))) {
                        triggerPreviewRefresh();
                    }
                });
                console.log('[FactorySync] Watching personas directory for external changes.');
            } catch (err) {
                console.error('[FactorySync] Failed to initialize personas watcher:', err);
            }
        }

        // 3. Lắng nghe sự kiện Đổi tên (Rename) trong Vault
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

        // 4. Lắng nghe sự kiện Chỉnh sửa (Modify) trong Vault
        this.registerEvent(
            this.app.vault.on('modify', (file) => {
                if (isAtomFile(file.path)) {
                    triggerPreviewRefresh();
                }
            })
        );

        // 5. Lắng nghe sự kiện Tạo mới (Create) trong Vault
        this.registerEvent(
            this.app.vault.on('create', (file) => {
                if (isAtomFile(file.path)) {
                    triggerPreviewRefresh();
                }
            })
        );

        // 6. Lắng nghe sự kiện Xóa (Delete) trong Vault
        this.registerEvent(
            this.app.vault.on('delete', (file) => {
                if (isAtomFile(file.path)) {
                    triggerPreviewRefresh();
                }
            })
        );
    }

    onunload() {
        if (this.personasWatcher) {
            try {
                this.personasWatcher.close();
                this.personasWatcher = null;
            } catch (e) {
                // Ignore cleanup errors
            }
        }
        console.log('[FactorySync] Plugin unloaded and watcher closed.');
    }
};
