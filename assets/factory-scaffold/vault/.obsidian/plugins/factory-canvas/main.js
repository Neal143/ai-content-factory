/**
 * factory-canvas - main.js
 * Last update: 25/08/2026 23:32 (GMT+7)
 * Vai tro: Obsidian Micro-Plugin chuyên trách điều khiển giao diện Canvas: Smooth Auto-Fit (Không giật/nhảy màn hình), 100% Kiểm soát cho User, Strict Membership & 1-Click Re-arrange.
 * Su dung khi: Chạy tự động trong Obsidian khi người dùng mở và tương tác trên file audience-hierarchy.canvas.
 * Output: 
 *   1. Mượt Mà & Êm Ái (Zero Jumping): Thao tác kéo thả, nối mũi tên diễn ra mượt mà, không bao giờ tự ý giật hay đẩy các thẻ khác.
 *   2. Gentle Group Auto-Fit: Khung Group tự co giãn ôm khít các thẻ con hợp pháp mà không làm xê dịch vị trí thẻ.
 *   3. Strict Membership: Chỉ thẻ có quan hệ phả hệ hợp pháp mới làm co giãn Khung Group.
 *   4. Silent Reverse-Sync: Cập nhật Frontmatter ngầm (Cạnh đáy -> Phả hệ, Cạnh bên -> Job Step) với khóa chống lặp tuyệt đối.
 *   5. 1-Click Re-arrange: Chỉ khi user chủ động bấm nút, toàn bộ sơ đồ mới được căn chỉnh lại theo lưới 5 cột.
 */

const { Plugin, Notice } = require('obsidian');

// -------------------------------------------------------------
// NHÓM 1: CẤU HÌNH HÌNH HỌC & MÀU SẮC CHUẨN (CANVAS_CONFIG)
// -------------------------------------------------------------
const CANVAS_CONFIG = {
    // Kích thước thẻ
    CARD_W: 540,
    CARD_H: 460,
    BIG_CARD_W: 640,
    BIG_CARD_H: 420,
    
    // Khoảng cách lưới
    GAP_X: 220,
    GAP_Y: 100,
    COLS: 5,
    
    // Tọa độ khởi đầu
    START_X: 100,
    START_Y: 620,
    
    // Đệm và phân tầng Khung Group
    PADDING_X: 60,
    PADDING_Y: 80,
    TIER_GAP: 160,
    MOTHER_OFFSET_Y: 150,
    
    // Bảng màu chuẩn
    COLOR_BIG: '1',
    COLOR_LITTLE: '4',
    COLOR_GROUP_L1: '4',
    COLOR_GROUP_L2: '5',
    COLOR_EDGE_PHẢ_HỆ: '4',
    COLOR_EDGE_JOB_STEP: '6'
};

module.exports = class FactoryCanvasPlugin extends Plugin {
    async onload() {
        console.log('[FactoryCanvas] Plugin loaded: Smooth & Jitter-Free Canvas Controller.');
        
        let canvasSyncDebounceTimer = null;
        let isInternalUpdating = false;
        let lastSyncTriggeredAt = 0;

        // -------------------------------------------------------------
        // NHÓM 2: HELPER FUNCTIONS (SLUG & YAML PARSER THEO DÒNG)
        // -------------------------------------------------------------
        const extractSlug = (text) => {
            if (!text) return null;
            const m = String(text).match(/\[\[(.*?)\]\]/);
            return m ? m[1].trim() : null;
        };

        const extractListField = (fmText, fieldName) => {
            const lines = fmText.replace(/\r\n/g, '\n').split('\n');
            let inField = false;
            const items = [];
            
            for (let i = 0; i < lines.length; i++) {
                const line = lines[i];
                const trimmed = line.trim();
                
                if (!inField) {
                    if (trimmed.startsWith(fieldName + ':')) {
                        inField = true;
                        const inlineVal = trimmed.substring((fieldName + ':').length).trim();
                        if (inlineVal.startsWith('[') && inlineVal.endsWith(']')) {
                            const inner = inlineVal.slice(1, -1).trim();
                            if (!inner) return [];
                            return inner.split(',').map(s => s.replace(/['"]/g, '').trim()).filter(Boolean);
                        }
                    }
                } else {
                    if (trimmed.startsWith('-')) {
                        let cleaned = trimmed.substring(1).trim();
                        cleaned = cleaned.replace(/^['"]/, '').replace(/['"]$/, '').trim();
                        if (cleaned) items.push(cleaned);
                    } else if (trimmed === '' || trimmed.startsWith('#')) {
                        continue;
                    } else {
                        break;
                    }
                }
            }
            return items;
        };

        const replaceListField = (fmText, fieldName, newItems) => {
            const lines = fmText.replace(/\r\n/g, '\n').split('\n');
            const resultLines = [];
            let inTargetField = false;
            let fieldFound = false;

            const newBlockLines = newItems.length > 0
                ? [`${fieldName}:`, ...newItems.map(item => `  - '${item}'`)]
                : [`${fieldName}: []`];

            for (let i = 0; i < lines.length; i++) {
                const line = lines[i];
                const trimmed = line.trim();

                if (!inTargetField) {
                    if (trimmed.startsWith(fieldName + ':')) {
                        inTargetField = true;
                        fieldFound = true;
                        resultLines.push(...newBlockLines);
                    } else {
                        resultLines.push(line);
                    }
                } else {
                    if (trimmed.startsWith('-') || trimmed === '' || trimmed.startsWith('#')) {
                        continue;
                    } else {
                        inTargetField = false;
                        resultLines.push(line);
                    }
                }
            }

            if (!fieldFound) {
                resultLines.push(...newBlockLines);
            }

            return resultLines.join('\n');
        };

        // Đọc trực tiếp nội dung Frontmatter từ đĩa (chính xác 100%, 0ms delay)
        const getVaultAudienceData = async () => {
            const audienceFiles = this.app.vault.getFiles().filter(f => 
                f.path.startsWith('01-Atomic/Audiences') && f.extension === 'md' && !f.name.startsWith('_')
            );
            const parentMap = {};
            const nextStepMap = {};
            for (const f of audienceFiles) {
                try {
                    const content = await this.app.vault.read(f);
                    if (content.startsWith('---')) {
                        const parts = content.split('---', 2);
                        if (parts.length >= 2) {
                            const parents = extractListField(parts[1], 'parent_audience');
                            const nextSteps = extractListField(parts[1], 'next_job_step');
                            parentMap[f.basename] = new Set(parents.map(p => String(p).replace(/\[\[|\]\]/g, '').trim()).filter(Boolean));
                            nextStepMap[f.basename] = new Set(nextSteps.map(s => String(s).replace(/\[\[|\]\]/g, '').trim()).filter(Boolean));
                        }
                    }
                } catch (e) {
                    parentMap[f.basename] = new Set();
                    nextStepMap[f.basename] = new Set();
                }
            }
            return { parentMap, nextStepMap };
        };

        const getVaultParentMap = async () => {
            const { parentMap } = await getVaultAudienceData();
            return parentMap;
        };

        // -------------------------------------------------------------
        // NHÓM 3: LIVE CANVAS IN-MEMORY SYNCHRONIZER (MƯỢT MÀ, 0 GIẬT DOM)
        // -------------------------------------------------------------
        const updateInMemoryCanvasNode = (nodeId, x, y, width, height, label) => {
            try {
                const leaves = this.app.workspace.getLeavesOfType('canvas');
                for (const leaf of leaves) {
                    const canvasObj = leaf.view?.canvas;
                    if (!canvasObj || !canvasObj.nodes) continue;
                    const nodeInst = canvasObj.nodes.get(nodeId);
                    if (nodeInst) {
                        if (x !== undefined) nodeInst.x = x;
                        if (y !== undefined) nodeInst.y = y;
                        if (width !== undefined) nodeInst.width = width;
                        if (height !== undefined) nodeInst.height = height;
                        if (label !== undefined && nodeInst.label !== undefined) nodeInst.label = label;
                        if (typeof nodeInst.render === 'function') nodeInst.render();
                    }

                    // Re-render tất cả edges kết nối với node vừa di chuyển
                    if (canvasObj.edges) {
                        for (const [, edgeInst] of canvasObj.edges) {
                            if (edgeInst.from?.node?.id === nodeId || edgeInst.to?.node?.id === nodeId) {
                                if (typeof edgeInst.render === 'function') edgeInst.render();
                            }
                        }
                    }
                }
            } catch (err) {
                console.warn('[FactoryCanvas] In-memory update error:', err);
            }
        };

        // -------------------------------------------------------------
        // NHÓM 4: GENTLE AUTO-FIT (CHỈ CO GIÃN KHUNG GROUP, KHÔNG DỊCH THẺ KHÁC)
        // -------------------------------------------------------------
        const autoFitGroups = async (canvasData, file) => {
            const groupNodes = (canvasData.nodes || []).filter(n => n.type === 'group');
            const textNodes = (canvasData.nodes || []).filter(n => n.type === 'text');
            const edges = canvasData.edges || [];
            
            const nodeById = {};
            for (const n of canvasData.nodes || []) {
                nodeById[n.id] = n;
                if (n.type === 'text') {
                    n.slug = extractSlug(n.text);
                }
            }
            
            let canvasModified = false;
            const vaultParentMap = await getVaultParentMap();

            const allLittleNodes = textNodes.filter(n => {
                if (n.color === CANVAS_CONFIG.COLOR_BIG || (n.text && n.text.includes('#big'))) return false;
                return n.slug && n.text && n.text.includes('#little');
            });

            // Dọn dẹp các group rác như 'Chưa liên kết cha'
            const initialNodeCount = canvasData.nodes.length;
            canvasData.nodes = canvasData.nodes.filter(n => {
                if (n.type === 'group' && (n.id === 'group_unlinked_audiences' || (n.label && n.label.includes('Chưa liên kết cha')))) {
                    try {
                        const leaves = this.app.workspace.getLeavesOfType('canvas');
                        for (const leaf of leaves) {
                            const canvasObj = leaf.view?.canvas;
                            if (canvasObj) {
                                const nodeInst = canvasObj.nodes?.get(n.id);
                                if (nodeInst) {
                                    if (typeof canvasObj.removeNode === 'function') {
                                        canvasObj.removeNode(nodeInst);
                                    } else {
                                        canvasObj.nodes.delete(n.id);
                                        if (nodeInst.nodeEl && typeof nodeInst.nodeEl.remove === 'function') {
                                            nodeInst.nodeEl.remove();
                                        }
                                    }
                                }
                            }
                        }
                    } catch (e) {}
                    return false;
                }
                return true;
            });
            if (canvasData.nodes.length !== initialNodeCount) {
                canvasModified = true;
            }

            for (const group of groupNodes) {
                // 1. Xác định Cha của Group từ Mũi tên hoặc Label
                const incomingEdge = edges.find(e => 
                    e.toNode === group.id && e.fromSide === 'bottom'
                );
                
                let parentSlug = null;
                if (incomingEdge) {
                    const fromNode = nodeById[incomingEdge.fromNode];
                    if (fromNode) {
                        parentSlug = extractSlug(fromNode.text || fromNode.label);
                    }
                }
                if (!parentSlug) {
                    parentSlug = extractSlug(group.label);
                }

                if (!parentSlug) {
                    // Group không có cha hợp pháp - bỏ qua
                    continue;
                }

                const targetLabel = `📦 NHÓM CON (Little Audiences): [[${parentSlug}]]`;
                if (group.label !== targetLabel) {
                    group.label = targetLabel;
                    canvasModified = true;
                    updateInMemoryCanvasNode(group.id, undefined, undefined, undefined, undefined, targetLabel);
                }

                // 2. Lọc danh sách thành viên hợp pháp theo Frontmatter
                const isMember = (node) => {
                    if (!node.slug) return false;
                    const pSet = vaultParentMap[node.slug];
                    return pSet && pSet.has(parentSlug);
                };

                const legitimateMembers = allLittleNodes.filter(n => isMember(n));

                // 3. AUTO-EJECT: CHỈ ĐẨY RA NGOÀI KHI THẺ NẰM TRONG KHUNG CỦA MẸ MÀ BỊ XÓA LIÊN KẾT
                const nonMembers = allLittleNodes.filter(n => !isMember(n));
                const currentGroupX = group.x;
                const currentGroupY = group.y;
                const currentGroupW = group.width;
                const currentGroupH = group.height;

                let ejectOffsetY = currentGroupY + currentGroupH + 60;

                for (const nm of nonMembers) {
                    const isInsideBox = nm.x >= (currentGroupX - 20) && (nm.x + nm.width) <= (currentGroupX + currentGroupW + 20) &&
                                       nm.y >= (currentGroupY - 20) && (nm.y + nm.height) <= (currentGroupY + currentGroupH + 20);
                    if (isInsideBox) {
                        nm.y = ejectOffsetY;
                        ejectOffsetY += (nm.height || CANVAS_CONFIG.CARD_H) + 60;
                        canvasModified = true;
                        updateInMemoryCanvasNode(nm.id, nm.x, nm.y);
                    }
                }

                // 4. CO GIÃN VIỀN KHUNG GROUP ÔM CÁC THẺ HỢP PHÁP
                if (legitimateMembers.length > 0) {
                    const minX = Math.min(...legitimateMembers.map(n => n.x));
                    const minY = Math.min(...legitimateMembers.map(n => n.y));
                    const maxRight = Math.max(...legitimateMembers.map(n => n.x + n.width));
                    const maxBottom = Math.max(...legitimateMembers.map(n => n.y + n.height));

                    const targetX = minX - CANVAS_CONFIG.PADDING_X;
                    const targetY = minY - CANVAS_CONFIG.PADDING_Y;
                    const targetW = maxRight - targetX + CANVAS_CONFIG.PADDING_X;
                    const targetH = maxBottom - targetY + CANVAS_CONFIG.PADDING_X;

                    const diffX = Math.abs(group.x - targetX);
                    const diffY = Math.abs(group.y - targetY);
                    const diffW = Math.abs(group.width - targetW);
                    const diffH = Math.abs(group.height - targetH);

                    if (diffX > 5 || diffY > 5 || diffW > 5 || diffH > 5) {
                        group.x = targetX;
                        group.y = targetY;
                        group.width = targetW;
                        group.height = targetH;
                        canvasModified = true;
                        updateInMemoryCanvasNode(group.id, targetX, targetY, targetW, targetH);

                        // Luôn bảo đảm Thẻ Mẹ Big Audience nằm ở chính giữa phía trên Khung Group 1
                        const bigNode = textNodes.find(n => n.color === CANVAS_CONFIG.COLOR_BIG || (n.text && n.text.includes('#big')));
                        if (bigNode && (!parentSlug || parentSlug === extractSlug(bigNode.text))) {
                            const newBigX = targetX + targetW / 2 - bigNode.width / 2;
                            const newBigY = targetY - bigNode.height - CANVAS_CONFIG.MOTHER_OFFSET_Y;
                            if (Math.abs(bigNode.x - newBigX) > 5 || Math.abs(bigNode.y - newBigY) > 5) {
                                bigNode.x = newBigX;
                                bigNode.y = newBigY;
                                updateInMemoryCanvasNode(bigNode.id, newBigX, newBigY);
                            }
                        }
                    }
                }
            }

            if (canvasModified) {
                isInternalUpdating = true;
                await this.app.vault.modify(file, JSON.stringify(canvasData, null, 2));
                isInternalUpdating = false;

                // Buộc Obsidian Canvas re-render toàn bộ edge routing sau khi node positions thay đổi
                try {
                    const leaves = this.app.workspace.getLeavesOfType('canvas');
                    for (const leaf of leaves) {
                        const canvasObj = leaf.view?.canvas;
                        if (!canvasObj) continue;

                        // Re-render từng edge trong bộ nhớ Canvas
                        if (canvasObj.edges) {
                            for (const [, edgeInst] of canvasObj.edges) {
                                if (typeof edgeInst.render === 'function') edgeInst.render();
                            }
                        }

                        // Yêu cầu Canvas vẽ lại toàn bộ frame
                        if (typeof canvasObj.requestFrame === 'function') {
                            canvasObj.requestFrame();
                        }
                    }
                } catch (err) {
                    console.warn('[FactoryCanvas] autoFitGroups: Error re-rendering edges:', err);
                }
            }
        };

        // -------------------------------------------------------------
        // NHÓM 5: SILENT ORIGIN-SIDE REVERSE-SYNC (ĐỒNG BỘ NGẦM)
        // -------------------------------------------------------------
        const syncCanvasToVault = async (canvasData, canvasFilePath) => {
            if (!canvasData || !canvasData.nodes || isInternalUpdating) return;
            if (!canvasFilePath.includes('audience-hierarchy')) return;

            const nodes = canvasData.nodes || [];
            const edges = canvasData.edges || [];

            const nodeById = {};
            const textNodes = [];

            for (const n of nodes) {
                nodeById[n.id] = n;
                if (n.type === 'text') {
                    const slug = extractSlug(n.text);
                    if (slug) {
                        n.slug = slug;
                        textNodes.push(n);
                    }
                }
            }

            const littleMemberNodes = textNodes.filter(n => n.color !== CANVAS_CONFIG.COLOR_BIG && n.slug && n.text.includes('#little'));

            // 1. Khởi tạo parentMap từ Frontmatter đĩa (Single Source of Truth) để không bị tọa độ kéo thả ghi đè
            const vaultParentMap = await getVaultParentMap();
            const parentMap = {};
            const nextStepMap = {};

            for (const tn of littleMemberNodes) {
                parentMap[tn.slug] = new Set(vaultParentMap[tn.slug] || []);
                nextStepMap[tn.slug] = new Set();
            }

            let canvasColorModified = false;

            for (const edge of edges) {
                const fromNode = nodeById[edge.fromNode];
                const toNode = nodeById[edge.toNode];
                if (!fromNode || !toNode) continue;

                const fromSide = edge.fromSide || 'right';

                // QUY TẮC 1: Xuất phát từ cạnh dưới (bottom) -> QUAN HỆ MẸ-CON
                if (fromSide === 'bottom') {
                    if (!edge.color) {
                        edge.color = CANVAS_CONFIG.COLOR_EDGE_PHẢ_HỆ;
                        canvasColorModified = true;
                    }
                    const fromSlug = extractSlug(fromNode.text || fromNode.label);
                    if (!fromSlug) continue;

                    // A. Mũi tên trỏ TRỰC TIẾP vào một Thẻ Text Node con
                    // Quy tắc: 1 audience chỉ có đúng 1 mẹ → THAY THẾ mẹ cũ
                    if (toNode.type === 'text' && toNode.slug) {
                        if (fromSlug !== toNode.slug) {
                            parentMap[toNode.slug] = new Set([fromSlug]);
                        }
                    }
                    // B. Mũi tên trỏ vào Khung Group → Gán parent cho TẤT CẢ thẻ thành viên bên trong group đó
                    else if (toNode.type === 'group') {
                        for (const tn of littleMemberNodes) {
                            if (fromSlug === tn.slug) continue;
                            // Kiểm tra thẻ có nằm bên trong bounding box của group không
                            const cX = tn.x + tn.width / 2;
                            const cY = tn.y + tn.height / 2;
                            const isInside = cX >= (toNode.x - 20) && cX <= (toNode.x + toNode.width + 20) &&
                                             cY >= (toNode.y - 20) && cY <= (toNode.y + toNode.height + 20);
                            if (isInside) {
                                parentMap[tn.slug] = new Set([fromSlug]);
                            }
                        }
                    }
                } 
                // QUY TẮC 2: Xuất phát từ cạnh bên (right hoặc left) -> QUAN HỆ JOB STEP
                else if (fromSide === 'right' || fromSide === 'left') {
                    if (!edge.color) {
                        edge.color = CANVAS_CONFIG.COLOR_EDGE_JOB_STEP;
                        canvasColorModified = true;
                    }
                    if (fromNode.type === 'text' && toNode.type === 'text') {
                        if (fromNode.slug && toNode.slug && fromNode.slug !== toNode.slug) {
                            if (!nextStepMap[fromNode.slug]) nextStepMap[fromNode.slug] = new Set();
                            nextStepMap[fromNode.slug].add(toNode.slug);
                        }
                    }
                }
            }

            if (canvasColorModified) {
                isInternalUpdating = true;
                const canvasFile = this.app.vault.getAbstractFileByPath(canvasFilePath);
                if (canvasFile) {
                    await this.app.vault.modify(canvasFile, JSON.stringify(canvasData, null, 2));
                }
                isInternalUpdating = false;
            }

            const audienceFiles = this.app.vault.getFiles().filter(f => 
                f.path.startsWith('01-Atomic/Audiences') && f.extension === 'md' && !f.name.startsWith('_')
            );

            let updatedCount = 0;

            // Bao trùm toàn bộ vòng lặp ghi frontmatter trong 1 block isInternalUpdating
            // để chặn triệt để cascade MD change events
            isInternalUpdating = true;
            try {
                for (const file of audienceFiles) {
                    const slug = file.basename;
                    if (!(slug in parentMap) && !(slug in nextStepMap)) continue;

                    const desiredParents = Array.from(parentMap[slug] || []).map(s => `[[${s}]]`);
                    const desiredNextSteps = Array.from(nextStepMap[slug] || []).map(s => `[[${s}]]`);

                    try {
                        let content = await this.app.vault.read(file);
                        content = content.replace(/\r\n/g, '\n');
                        if (!content.startsWith('---')) continue;

                        const parts = content.split('---', 2);
                        if (parts.length < 2) continue;

                        let fm = parts[1];
                        const body = content.substring(parts[1].length + 6);

                        const currentParents = extractListField(fm, 'parent_audience');
                        const currentNextSteps = extractListField(fm, 'next_job_step');

                        const isParentEqual = JSON.stringify(currentParents.sort()) === JSON.stringify(desiredParents.sort());
                        const isNextEqual = JSON.stringify(currentNextSteps.sort()) === JSON.stringify(desiredNextSteps.sort());

                        if (isParentEqual && isNextEqual) {
                            continue;
                        }

                        if (!isParentEqual) {
                            fm = replaceListField(fm, 'parent_audience', desiredParents);
                        }
                        if (!isNextEqual) {
                            fm = replaceListField(fm, 'next_job_step', desiredNextSteps);
                        }

                        const newFullContent = `---${fm}---${body}`;
                        await this.app.vault.modify(file, newFullContent);
                        updatedCount++;
                    } catch (err) {
                        console.error(`[FactoryCanvas] Loi khi cap nhat file ${file.path}:`, err);
                    }
                }
            } finally {
                isInternalUpdating = false;
            }

            if (updatedCount > 0) {
                new Notice(`[Factory Canvas] 🔄 Đã đồng bộ quan hệ vào ${updatedCount} file Audience`, 2500);
                // Re-arrange duy nhất 1 lần sau khi tất cả frontmatter đã cập nhật xong
                clearTimeout(canvasSyncDebounceTimer);
                lastSyncTriggeredAt = Date.now();
                canvasSyncDebounceTimer = setTimeout(async () => {
                    await reArrangeCanvasLayout(false);
                }, 200);
            }
            return updatedCount;
        };

        // -------------------------------------------------------------
        // NHÓM 6: RE-ARRANGE CANVAS ENGINE (TỰ ĐỘNG HOẶC 1-CLICK MANUAL)
        // -------------------------------------------------------------
        const reArrangeCanvasLayout = async (isManual = true) => {
            const leaves = this.app.workspace.getLeavesOfType('canvas');
            let targetCanvasLeaf = leaves.find(l => l.view?.file?.path?.includes('audience-hierarchy')) || leaves[0];
            
            if (!targetCanvasLeaf || !targetCanvasLeaf.view?.file) {
                if (isManual) new Notice('⚠️ Hãy mở file audience-hierarchy.canvas trước khi căn chỉnh!', 4000);
                return;
            }

            const canvasFile = targetCanvasLeaf.view.file;
            const raw = await this.app.vault.read(canvasFile);
            const canvasData = JSON.parse(raw);

            // 0. Lọc bỏ triệt để các group rác không có cha hợp pháp hoặc group unlinked ngay từ đầu
            canvasData.nodes = (canvasData.nodes || []).filter(n => {
                if (n.type === 'group') {
                    if (n.id === 'group_unlinked_audiences' || (n.label && n.label.includes('Chưa liên kết cha'))) {
                        return false;
                    }
                }
                return true;
            });

            const nodes = canvasData.nodes;
            const textNodes = nodes.filter(n => n.type === 'text');
            const groupNodes = nodes.filter(n => n.type === 'group');

            const bigNode = textNodes.find(n => n.color === CANVAS_CONFIG.COLOR_BIG || (n.text && n.text.includes('#big')));
            const bigSlug = bigNode ? extractSlug(bigNode.text) : null;
            const littleNodes = textNodes.filter(n => n.color !== CANVAS_CONFIG.COLOR_BIG && n.text && n.text.includes('#little'));

            const CARD_W = CANVAS_CONFIG.CARD_W;
            const CARD_H = CANVAS_CONFIG.CARD_H;
            const GAP_X = CANVAS_CONFIG.GAP_X;
            const GAP_Y = CANVAS_CONFIG.GAP_Y;
            const COLS = CANVAS_CONFIG.COLS;
            const START_X = CANVAS_CONFIG.START_X;
            const START_Y = CANVAS_CONFIG.START_Y;

            const vaultParentMap = await getVaultParentMap();

            // 1. Phân nhóm thẻ theo Cây Phả Hệ thực tế trong Frontmatter
            const nodesByParent = {};
            const unlinkedNodes = [];

            for (const node of littleNodes) {
                node.slug = extractSlug(node.text);
                const pSet = vaultParentMap[node.slug];
                if (pSet && pSet.size > 0) {
                    for (const p of pSet) {
                        if (!nodesByParent[p]) nodesByParent[p] = [];
                        if (!nodesByParent[p].includes(node)) nodesByParent[p].push(node);
                    }
                } else {
                    unlinkedNodes.push(node);
                }
            }

            // Thẻ thuộc Level 1 (con của Big)
            let level1Nodes = (bigSlug && nodesByParent[bigSlug]) ? nodesByParent[bigSlug] : [];
            if (level1Nodes.length === 0) {
                level1Nodes = littleNodes.filter(n => !unlinkedNodes.includes(n));
            }

            // Tách Level 1: Leaf ở trên, Branching (có con) ở HÀNG ĐÁY
            const leafNodes = level1Nodes.filter(n => !nodesByParent[n.slug] || nodesByParent[n.slug].length === 0);
            const branchingNodes = level1Nodes.filter(n => nodesByParent[n.slug] && nodesByParent[n.slug].length > 0);
            const sortedLevel1 = [...leafNodes, ...branchingNodes];

            // 2. Bố trí Lưới 5 cột cho Level 1 (Group 1)
            for (let idx = 0; idx < sortedLevel1.length; idx++) {
                const node = sortedLevel1[idx];
                const col = idx % COLS;
                const row = Math.floor(idx / COLS);
                node.x = START_X + col * (CARD_W + GAP_X);
                node.y = START_Y + row * (CARD_H + GAP_Y);
                node.width = CARD_W;
                node.height = CARD_H;
            }

            // 3. Tính Bounding Box Group 1 & Căn Big Audience ở ĐƯỜNG CHÍNH TRỰC
            let l1_minX = START_X;
            let l1_minY = START_Y;
            let l1_maxRight = START_X + COLS * (CARD_W + GAP_X) - GAP_X;
            let l1_maxBottom = START_Y + Math.ceil(sortedLevel1.length / COLS) * (CARD_H + GAP_Y) - GAP_Y;

            if (sortedLevel1.length > 0) {
                l1_minX = Math.min(...sortedLevel1.map(n => n.x));
                l1_minY = Math.min(...sortedLevel1.map(n => n.y));
                l1_maxRight = Math.max(...sortedLevel1.map(n => n.x + n.width));
                l1_maxBottom = Math.max(...sortedLevel1.map(n => n.y + n.height));
            }

            const l1_groupW = l1_maxRight - (l1_minX - CANVAS_CONFIG.PADDING_X) + CANVAS_CONFIG.PADDING_X;
            const l1_groupH = l1_maxBottom - (l1_minY - CANVAS_CONFIG.PADDING_Y) + CANVAS_CONFIG.PADDING_X;
            const l1_centerX = (l1_minX - CANVAS_CONFIG.PADDING_X) + l1_groupW / 2;

            const mainGroupNode = groupNodes.find(g => {
                const ps = extractSlug(g.label);
                return ps === bigSlug;
            });

            if (mainGroupNode) {
                mainGroupNode.x = l1_minX - CANVAS_CONFIG.PADDING_X;
                mainGroupNode.y = l1_minY - CANVAS_CONFIG.PADDING_Y;
                mainGroupNode.width = l1_groupW;
                mainGroupNode.height = l1_groupH;
            }

            if (bigNode) {
                bigNode.width = CANVAS_CONFIG.BIG_CARD_W;
                bigNode.height = CANVAS_CONFIG.BIG_CARD_H;
                bigNode.x = l1_centerX - bigNode.width / 2;
                bigNode.y = (l1_minY - CANVAS_CONFIG.PADDING_Y) - bigNode.height - CANVAS_CONFIG.MOTHER_OFFSET_Y;
            }

            // 4. Bố trí các Khung Group Level 2+ (Tầng dưới, căn chính trực theo thẻ cha)
            let currentTierY = (l1_minY - CANVAS_CONFIG.PADDING_Y) + l1_groupH + CANVAS_CONFIG.TIER_GAP;

            for (const [pSlug, children] of Object.entries(nodesByParent)) {
                if (pSlug === bigSlug || children.length === 0) continue;

                const parentCard = textNodes.find(n => n.slug === pSlug) || sortedLevel1[sortedLevel1.length - 1];
                const parentCenterX = parentCard ? (parentCard.x + parentCard.width / 2) : l1_centerX;

                const subCols = Math.min(children.length, COLS);
                const subRows = Math.ceil(children.length / subCols);
                const subBlockW = subCols * (CARD_W + GAP_X) - GAP_X;
                const subBlockH = subRows * (CARD_H + GAP_Y) - GAP_Y;

                const subGroupW = subBlockW + 120;
                const subGroupH = subBlockH + 140;
                const subGroupX = parentCenterX - subGroupW / 2;
                const subGroupY = currentTierY;

                for (let cIdx = 0; cIdx < children.length; cIdx++) {
                    const cNode = children[cIdx];
                    const cCol = cIdx % subCols;
                    const cRow = Math.floor(cIdx / subCols);
                    cNode.x = subGroupX + 60 + cCol * (CARD_W + GAP_X);
                    cNode.y = subGroupY + 80 + cRow * (CARD_H + GAP_Y);
                    cNode.width = CARD_W;
                    cNode.height = CARD_H;
                }

                let subGroupNode = groupNodes.find(g => extractSlug(g.label) === pSlug);
                if (!subGroupNode && children.length > 1) {
                    subGroupNode = {
                        id: `group_sub_${pSlug}`,
                        type: "group",
                        label: `📦 NHÓM CON (Little Audiences): [[${pSlug}]]`,
                        x: subGroupX,
                        y: subGroupY,
                        width: subGroupW,
                        height: subGroupH,
                        color: CANVAS_CONFIG.COLOR_GROUP_L2
                    };
                    canvasData.nodes.unshift(subGroupNode);
                    groupNodes.push(subGroupNode);
                } else if (subGroupNode) {
                    subGroupNode.x = subGroupX;
                    subGroupNode.y = subGroupY;
                    subGroupNode.width = subGroupW;
                    subGroupNode.height = subGroupH;
                    subGroupNode.label = `📦 NHÓM CON (Little Audiences): [[${pSlug}]]`;
                }

                currentTierY += (children.length > 1 ? subGroupH : CARD_H) + CANVAS_CONFIG.TIER_GAP;
            }

            // 5. Bố trí các thẻ Unlinked (nếu có) ở hàng dưới cùng dạng thẻ độc lập, KHÔNG TẠO KHUNG GROUP
            if (unlinkedNodes.length > 0) {
                const uCols = Math.min(unlinkedNodes.length, COLS);
                const uRows = Math.ceil(unlinkedNodes.length / uCols);

                for (let uIdx = 0; uIdx < unlinkedNodes.length; uIdx++) {
                    const uNode = unlinkedNodes[uIdx];
                    const uCol = uIdx % uCols;
                    const uRow = Math.floor(uIdx / uCols);
                    uNode.x = START_X + uCol * (CARD_W + GAP_X);
                    uNode.y = currentTierY + uRow * (CARD_H + GAP_Y);
                    uNode.width = CARD_W;
                    uNode.height = CARD_H;
                }

                currentTierY += uRows * (CARD_H + GAP_Y) + CANVAS_CONFIG.TIER_GAP;
            }

            // Dọn dẹp bất kỳ group rác "Chưa liên kết cha" nào còn sót lại
            canvasData.nodes = canvasData.nodes.filter(n => {
                if (n.type === 'group') {
                    if (n.id === 'group_unlinked_audiences' || (n.label && n.label.includes('Chưa liên kết cha'))) {
                        return false;
                    }
                }
                return true;
            });

            // 6. XÂY DỰNG & TÁI CẤU TRÚC TOÀN BỘ MŨI TÊN (RE-ARRANGE ALL EDGES)
            const { nextStepMap: vNextStepMap } = await getVaultAudienceData();
            const nodeIdBySlug = {};
            for (const n of textNodes) {
                if (n.slug) nodeIdBySlug[n.slug] = n.id;
            }

            // Ghi nhớ màu tùy biến của user nếu có
            const oldEdges = canvasData.edges || [];
            const userColorMap = {};
            for (const oe of oldEdges) {
                if (oe.fromNode && oe.toNode && oe.color) {
                    userColorMap[`${oe.fromNode}->${oe.toNode}`] = oe.color;
                }
            }

            const newEdges = [];
            let edgeCounter = 1;

            // A. Mũi tên Phả hệ Big Audience -> Group 1 (hoặc thẻ con đơn lẻ)
            if (bigNode) {
                if (level1Nodes.length > 1 && mainGroupNode) {
                    const pairKey = `${bigNode.id}->${mainGroupNode.id}`;
                    newEdges.push({
                        id: "edge_root_to_group",
                        fromNode: bigNode.id,
                        fromSide: "bottom",
                        toNode: mainGroupNode.id,
                        toSide: "top",
                        color: userColorMap[pairKey] || CANVAS_CONFIG.COLOR_EDGE_PHẢ_HỆ
                    });
                } else if (level1Nodes.length === 1) {
                    const singleChildId = nodeIdBySlug[level1Nodes[0].slug];
                    if (singleChildId) {
                        const pairKey = `${bigNode.id}->${singleChildId}`;
                        newEdges.push({
                            id: "edge_root_to_single_child",
                            fromNode: bigNode.id,
                            fromSide: "bottom",
                            toNode: singleChildId,
                            toSide: "top",
                            color: userColorMap[pairKey] || CANVAS_CONFIG.COLOR_EDGE_PHẢ_HỆ
                        });
                    }
                }
            }

            // B. Mũi tên Phả hệ Level 2+ Sub-groups
            for (const [pSlug, children] of Object.entries(nodesByParent)) {
                if (pSlug === bigSlug || children.length === 0) continue;
                const pNodeId = nodeIdBySlug[pSlug];
                const sgNode = groupNodes.find(g => extractSlug(g.label) === pSlug);

                if (children.length > 1 && pNodeId && sgNode) {
                    const pairKey = `${pNodeId}->${sgNode.id}`;
                    newEdges.push({
                        id: `edge_pha_he_sub_${edgeCounter++}`,
                        fromNode: pNodeId,
                        fromSide: "bottom",
                        toNode: sgNode.id,
                        toSide: "top",
                        color: userColorMap[pairKey] || CANVAS_CONFIG.COLOR_EDGE_PHẢ_HỆ
                    });
                } else if (children.length === 1 && pNodeId) {
                    const singleChildId = nodeIdBySlug[children[0].slug];
                    if (singleChildId) {
                        const pairKey = `${pNodeId}->${singleChildId}`;
                        newEdges.push({
                            id: `edge_pha_he_sub_single_${edgeCounter++}`,
                            fromNode: pNodeId,
                            fromSide: "bottom",
                            toNode: singleChildId,
                            toSide: "top",
                            color: userColorMap[pairKey] || CANVAS_CONFIG.COLOR_EDGE_PHẢ_HỆ
                        });
                    }
                }
            }

            // C. Mũi tên Tiến trình Job Steps
            for (const [fromSlug, toSlugs] of Object.entries(vNextStepMap)) {
                const fromId = nodeIdBySlug[fromSlug];
                if (!fromId) continue;

                for (const toSlug of toSlugs) {
                    const toId = nodeIdBySlug[toSlug];
                    if (toId && toId !== fromId) {
                        const pairKey = `${fromId}->${toId}`;
                        newEdges.push({
                            id: `edge_job_step_${edgeCounter++}`,
                            fromNode: fromId,
                            fromSide: "right",
                            toNode: toId,
                            toSide: "left",
                            color: userColorMap[pairKey] || CANVAS_CONFIG.COLOR_EDGE_JOB_STEP
                        });
                    }
                }
            }

            canvasData.edges = newEdges;

            // 7. Ghi đĩa Canvas Data
            isInternalUpdating = true;
            await this.app.vault.modify(canvasFile, JSON.stringify(canvasData, null, 2));
            isInternalUpdating = false;

            // 8. Tải lại toàn bộ View trong RAM: Xóa các node/edge không còn tồn tại
            try {
                const canvasObj = targetCanvasLeaf.view?.canvas;
                if (canvasObj) {
                    const validNodeIds = new Set(canvasData.nodes.map(n => n.id));
                    if (canvasObj.nodes) {
                        for (const [nodeId, nodeInst] of Array.from(canvasObj.nodes.entries())) {
                            if (!validNodeIds.has(nodeId)) {
                                if (typeof canvasObj.removeNode === 'function') {
                                    canvasObj.removeNode(nodeInst);
                                } else {
                                    canvasObj.nodes.delete(nodeId);
                                    if (nodeInst.nodeEl && typeof nodeInst.nodeEl.remove === 'function') {
                                        nodeInst.nodeEl.remove();
                                    }
                                }
                            }
                        }
                    }

                    const validEdgeIds = new Set(canvasData.edges.map(e => e.id));
                    if (canvasObj.edges) {
                        for (const [edgeId, edgeInst] of Array.from(canvasObj.edges.entries())) {
                            if (!validEdgeIds.has(edgeId)) {
                                if (typeof canvasObj.removeEdge === 'function') {
                                    canvasObj.removeEdge(edgeInst);
                                } else {
                                    canvasObj.edges.delete(edgeId);
                                    if (edgeInst.lineEl && typeof edgeInst.lineEl.remove === 'function') {
                                        edgeInst.lineEl.remove();
                                    }
                                }
                            }
                        }
                    }

                    if (typeof canvasObj.setData === 'function') {
                        canvasObj.setData(canvasData);
                    }
                    if (typeof canvasObj.requestSave === 'function') {
                        canvasObj.requestSave();
                    }

                    // Buộc Obsidian re-render edge routing sau khi setData nạp xong
                    setTimeout(() => {
                        try {
                            if (canvasObj.edges) {
                                for (const [, edgeInst] of canvasObj.edges) {
                                    if (typeof edgeInst.render === 'function') edgeInst.render();
                                }
                            }
                            if (typeof canvasObj.requestFrame === 'function') {
                                canvasObj.requestFrame();
                            }
                        } catch (e) {
                            console.warn('[FactoryCanvas] reArrange edge re-render error:', e);
                        }
                    }, 100);

                    if (isManual && typeof canvasObj.zoomToFit === 'function') {
                        setTimeout(() => canvasObj.zoomToFit(), 250);
                    }
                }
            } catch (err) {
                console.warn('[FactoryCanvas] Error refreshing canvas view:', err);
            }

            if (isManual) {
                new Notice('✨ [Factory Canvas] Đã căn chỉnh sơ đồ theo trục chính trực và ngữ nghĩa chuẩn 100%!', 3000);
            }
        };

        // -------------------------------------------------------------
        // NHÓM 7: ĐĂNG KÝ CÁC ĐIỂM TRUY CẬP (CANVAS HEADER & COMMAND & CONTEXT MENU)
        // -------------------------------------------------------------
        
        // 1. Command Palette (Ctrl + P)
        this.addCommand({
            id: 'rearrange-audience-canvas',
            name: '🪄 Căn chỉnh lại toàn bộ sơ đồ Audience Canvas (Re-arrange Layout)',
            callback: async () => {
                await reArrangeCanvasLayout(true);
            }
        });

        // 2. Canvas View Header Action Button
        const attachHeaderButton = () => {
            const leaves = this.app.workspace.getLeavesOfType('canvas');
            for (const leaf of leaves) {
                if (leaf.view && !leaf.view._hasFactoryRearrangeBtn) {
                    leaf.view._hasFactoryRearrangeBtn = true;
                    if (typeof leaf.view.addAction === 'function') {
                        leaf.view.addAction('sparkles', 'Căn chỉnh sơ đồ Canvas (Re-arrange)', async () => {
                            await reArrangeCanvasLayout(true);
                        });
                    }
                }
            }
        };

        this.registerEvent(this.app.workspace.on('layout-change', attachHeaderButton));
        this.registerEvent(this.app.workspace.on('active-leaf-change', attachHeaderButton));
        attachHeaderButton();

        // 3. Right-Click Context Menu trên Canvas
        this.registerEvent(
            this.app.workspace.on('canvas:menu', (menu, canvas) => {
                menu.addItem((item) => {
                    item.setTitle('🪄 Căn chỉnh lại sơ đồ (Re-arrange Layout)')
                        .setIcon('sparkles')
                        .onClick(async () => {
                            await reArrangeCanvasLayout(true);
                        });
                });
            })
        );

        // -------------------------------------------------------------
        // NHÓM 8: OBSIDIAN CANVAS & VAULT REAL-TIME HOOKS (DEBOUNCED & SILENT)
        // -------------------------------------------------------------
        const handleAudienceMdChange = async () => {
            if (isInternalUpdating) return;
            // Bỏ qua nếu syncCanvasToVault vừa trigger re-arrange trong 1 giây gần nhất
            if (Date.now() - lastSyncTriggeredAt < 1000) return;
            const canvasFile = this.app.vault.getAbstractFileByPath('03-Content/Content Plan/audience-hierarchy.canvas');
            if (canvasFile) {
                clearTimeout(canvasSyncDebounceTimer);
                canvasSyncDebounceTimer = setTimeout(async () => {
                    try {
                        await reArrangeCanvasLayout(false);
                    } catch (e) {
                        console.error('[FactoryCanvas] Error auto-rearranging on MD change:', e);
                    }
                }, 300);
            }
        };

        this.registerEvent(
            this.app.vault.on('modify', async (file) => {
                // 1. Khi file Canvas bị sửa bởi thao tác của User
                if (file.extension === 'canvas' && file.path.includes('audience-hierarchy')) {
                    if (isInternalUpdating) return;
                    clearTimeout(canvasSyncDebounceTimer);
                    canvasSyncDebounceTimer = setTimeout(async () => {
                        try {
                            const raw = await this.app.vault.read(file);
                            const canvasData = JSON.parse(raw);
                            
                            // Đồng bộ Mũi tên ngầm vào Frontmatter
                            const syncCount = await syncCanvasToVault(canvasData, file.path);

                            // Chỉ co giãn Group khi không có thay đổi frontmatter
                            // (nếu có thay đổi, syncCanvasToVault đã schedule reArrangeCanvasLayout)
                            if (syncCount === 0) {
                                await autoFitGroups(canvasData, file);
                            }
                        } catch (e) {
                            console.error('[FactoryCanvas] Error handling canvas modify:', e);
                        }
                    }, 300);
                }
                // 2. Khi file Audience Markdown bị sửa frontmatter ngoài Canvas
                else if (file.extension === 'md' && file.path.startsWith('01-Atomic/Audiences')) {
                    await handleAudienceMdChange();
                }
            })
        );

        this.registerEvent(
            this.app.metadataCache.on('changed', async (file) => {
                if (file.path.startsWith('01-Atomic/Audiences')) {
                    await handleAudienceMdChange();
                }
            })
        );
    }

    onunload() {
        console.log('[FactoryCanvas] Plugin unloaded.');
    }
};
