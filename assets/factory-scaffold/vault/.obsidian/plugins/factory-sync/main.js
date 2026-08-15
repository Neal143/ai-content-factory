const { Plugin, Notice } = require('obsidian');
const { spawn } = require('child_process');
const path = require('path');

module.exports = class FactorySyncPlugin extends Plugin {
    async onload() {
        console.log('[FactorySync] Plugin loaded.');
        
        let debounceTimer = null;
        
        this.registerEvent(
            this.app.vault.on('rename', (file, oldPath) => {
                if (!file.path.endsWith('.md')) return;
                
                const oldBase = path.basename(oldPath, '.md');
                const newBase = path.basename(file.path, '.md');
                
                if (oldBase === newBase) return;
                
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => {
                    const factoryRoot = path.resolve(this.app.vault.adapter.basePath, '..');
                    const scriptPath = path.join(factoryRoot, '.agents', 'scripts', 'safe_rename.py');
                    
                    const args = [
                        scriptPath,
                        '--old-name', oldBase,
                        '--new-name', newBase,
                        '--sync-only',
                        '--scan-root', factoryRoot
                    ];
                    
                    const proc = spawn('python', args, { 
                        cwd: factoryRoot,
                        windowsHide: true
                    });
                    
                    let stdout = '';
                    let stderr = '';
                    
                    proc.stdout.on('data', (d) => stdout += d.toString());
                    proc.stderr.on('data', (d) => stderr += d.toString());
                    
                    proc.on('close', (code) => {
                        if (code !== 0) {
                            console.error('[FactorySync] Sync Error:', stderr);
                            new Notice(`[Factory Sync] ❌ Lỗi đồng bộ: ${stderr || 'Process exited with code ' + code}`, 5000);
                            return;
                        }
                        try {
                            const res = JSON.parse(stdout);
                            new Notice(`[Factory Sync] 🔄 Đã đồng bộ ${res.total_files_updated} file trong Content Factory`, 4000);
                        } catch (e) {
                            new Notice(`[Factory Sync] 🔄 Đã đồng bộ tham chiếu file thành công!`, 4000);
                        }
                    });
                }, 300);
            })
        );
    }

    onunload() {
        console.log('[FactorySync] Plugin unloaded.');
    }
};
