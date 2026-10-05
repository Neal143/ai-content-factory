/**
 * factory-canvas - main.js
 * Last update: 05/10/2026 15:10 (GMT+7)
 * Vai tro: Obsidian Micro-Plugin chuyen trach dieu khien giao dien Canvas: Live RAM Data Extractor, Spatial Group Isolation, Gentle Auto-Fit, Bidirectional Edge Sync, Safe Undo Protection, Structured Debug Logging, 1-Click Re-arrange & Flyout Auto-Center.
 * Su dung khi: Chạy tự động trong Obsidian khi người dùng mở và tương tác trên file audience-hierarchy.canvas.
 * Output: 
 *   1. Smart Snap: Noi edge cha->con khi cha da co Group -> the con tu xep vao o trong ke tiep, Group chi no ra, node phia duoi bi day xuong deu; khong co Group -> giu nguyen vi tri. Gop vao 1 buoc Undo.
 *   2. Member Fit: Vi tri the KHONG quyet dinh quan he cha-con. Tha the con o dau -> 400ms sau Group cua cha co gian om tron cac the con (theo FM), trung cong thuc renderer, gop vao 1 buoc Undo. Go quan he: xoa mui ten hoac sua FM.
 *   3. Time-Lock Cascade Suppress: Chốt chặn 1500ms dập tắt hoàn toàn vòng lặp đệ quy giữa requestSave và vault.on('modify').
 *   4. Safe Undo Protection: Bảo toàn 100% Undo Stack đơn nhất (chỉ cần 1 lần Ctrl+Z để hoàn tác quan hệ cha-con).
 *   5. Structured Debug Logging: Minh bạch hóa toàn bộ trạng thái hệ thống với các log có tiền tố [FactoryCanvas][SYNC/SNAP/FIT/UNDO].
 *   6. 1-Click Re-arrange & Flyout Auto-Center: Căn chỉnh toàn diện sơ đồ và đưa trọng tâm về giữa màn hình.
 */

const { Plugin, Notice, setIcon } = require('obsidian');

// -------------------------------------------------------------
// NHÓM 1: CẤU HÌNH HÌNH HỌC & MÀU SẮC CHUẨN (CANVAS_CONFIG)
// -------------------------------------------------------------
const CANVAS_CONFIG = {
    // Kích thước thẻ chuẩn
    CARD_W: 540,
    CARD_H: 460,
    ROOT_CARD_W: 640,
    ROOT_CARD_H: 420,
    // Alias tương thích ngược
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
    
    // Bảng màu chuẩn (Graph-driven colors)
    COLOR_ROOT: '1',
    COLOR_CHILD: '4',
    COLOR_BIG: '1',
    COLOR_LITTLE: '4',
    COLOR_GROUP_L1: '4',
    COLOR_GROUP_L2: '5',
    COLOR_EDGE_PHA_HE: '4',
    COLOR_EDGE_PHẢ_HỆ: '4',
    COLOR_EDGE_JOB_STEP: '6'
};

// -------------------------------------------------------------
// NHÓM 1.5: SMART SNAP (HAM THUAN, KHONG PHU THUOC OBSIDIAN - TEST DUOC BANG NODE)
// Xep the vua duoc noi cha vao o trong ke tiep trong luoi Group cua cha.
// Cong thuc trung khop compute_bounding_box cua render_audience_canvas.py
// (pad trai/phai/duoi = PADDING_X, pad tren = PADDING_Y) de renderer khong ghi de ket qua.
// -------------------------------------------------------------
const slugOfNode = (n) => {
    const m = String((n && (n.text || n.label)) || '').match(/\[\[(.*?)\]\]/);
    return m ? m[1].trim() : null;
};

const isNodeInsideGroup = (n, g, tol = 30) => (
    n.x >= g.x - tol &&
    n.x + n.width <= g.x + g.width + tol &&
    n.y >= g.y - tol &&
    n.y + n.height <= g.y + g.height + tol
);

/**
 * computeGroupSnap(data, childId, parentSlug, directEdgeId)
 * Input : data = canvas.getData(); childId = id the con; parentSlug = slug cha; directEdgeId = id mui ten cha->con user vua ve.
 * Output: { data, moved, slot, shiftY } (ban sao da sua) hoac null neu cha chua co Group / khong tim thay the con.
 */
const computeGroupSnap = (data, childId, parentSlug, directEdgeId) => {
    const out = JSON.parse(JSON.stringify(data));
    const nodes = out.nodes || [];
    const group = nodes.find(n => n.type === 'group' && slugOfNode(n) === parentSlug);
    const child = nodes.find(n => n.id === childId);
    if (!group || !child) return null;
    const parent = nodes.find(n => n.type === 'text' && slugOfNode(n) === parentSlug) || null;

    const { CARD_W, CARD_H, GAP_X, GAP_Y, COLS, PADDING_X, PADDING_Y } = CANVAS_CONFIG;
    const stepX = CARD_W + GAP_X;
    const stepY = CARD_H + GAP_Y;
    let moved = false, slot = -1, shiftY = 0;

    if (!isNodeInsideGroup(child, group)) {
        // 1. Tim o trong dau tien (duyet theo hang, toi da COLS cot) trong luoi cua Group
        const originX = group.x + PADDING_X;
        const originY = group.y + PADDING_Y;
        // O bi chiem = o chong lan (tinh ca nua khoang cach luoi) voi bat ky the nao dang nam trong Group.
        // Kiem tra chong lan thay vi lam tron toa do: Group co the da no lech luoi (Member Fit / user keo the).
        const blockers = nodes.filter(n => n.type === 'text' && n !== child && n !== parent && isNodeInsideGroup(n, group));
        const isSlotFree = (sx, sy) => !blockers.some(n =>
            n.x < sx + CARD_W + GAP_X / 2 && n.x + n.width > sx - GAP_X / 2 &&
            n.y < sy + CARD_H + GAP_Y / 2 && n.y + n.height > sy - GAP_Y / 2
        );
        slot = 0;
        while (!isSlotFree(originX + (slot % COLS) * stepX, originY + Math.floor(slot / COLS) * stepY)) slot++;
        child.x = originX + (slot % COLS) * stepX;
        child.y = originY + Math.floor(slot / COLS) * stepY;
        child.width = CARD_W;
        child.height = CARD_H;
        moved = true;

        // 2. Chi NOI Group (khong co) de om the moi
        const oldWidth = group.width;
        const oldBottom = group.y + group.height;
        const newRight = Math.max(group.x + group.width, child.x + CARD_W + PADDING_X);
        const newBottom = Math.max(oldBottom, child.y + CARD_H + PADDING_X);
        group.width = newRight - group.x;
        group.height = newBottom - group.y;

        // 3. Group cao them -> day moi node nam duoi day cu xuong dung phan tang them (tranh chong lan tang duoi)
        shiftY = newBottom - oldBottom;
        if (shiftY > 0) {
            for (const n of nodes) {
                if (n !== group && n !== child && n.y >= oldBottom) n.y += shiftY;
            }
        }

        // 4. Group rong ra va cha la Big Audience -> can giua the cha phia tren Group (giong renderer)
        if (parent && group.width !== oldWidth && String(parent.text || '').includes('`#big`')) {
            parent.x = group.x + group.width / 2 - parent.width / 2;
        }

        // 5. Dua the con xuong cuoi mang de importData nang zIndex len tren Group (khong bi Group che)
        out.nodes = nodes.filter(n => n !== child).concat([child]);
    }

    // 6. Mui ten: da co Cha->Group thi bo Cha->The (renderer chi sinh Cha->Group); chua co thi thay bang edge moi Cha->Group
    const edges = out.edges || [];
    const directEdge = edges.find(e => e.id === directEdgeId);
    if (directEdge) {
        const hasGroupEdge = parent && edges.some(e => e.fromNode === parent.id && e.fromSide === 'bottom' && e.toNode === group.id);
        out.edges = edges.filter(e => e !== directEdge);
        if (!hasGroupEdge && parent) {
            out.edges.push({ ...directEdge, id: `${directEdge.id}_grp`, toNode: group.id, toSide: 'top' });
        }
    }
    return { data: out, moved, slot, shiftY };
};

/**
 * computeGroupFit(data, membersByParent)
 * Input : data = canvas.getData(); membersByParent = { slugCha: [slugCon, ...] } lay tu Frontmatter.
 * Output: { data, fitted: [slugCha...] } (ban sao da sua) hoac null neu khong Group nao can doi.
 * Logic : Khung Group cua cha P = bounding box cac the con (theo FM) tai vi tri thuc te, trung cong thuc
 *         compute_bounding_box cua renderer (trai/phai/duoi = PADDING_X, tren = PADDING_Y).
 *         Chi xu ly Group co >= 2 the con (renderer chi tao Group khi > 1 con).
 *         Group cua Big Audience doi -> dat lai the Big chinh giua phia tren Group (giong renderer).
 */
const computeGroupFit = (data, membersByParent) => {
    const out = JSON.parse(JSON.stringify(data));
    const nodes = out.nodes || [];
    const { PADDING_X, PADDING_Y, BIG_CARD_W, BIG_CARD_H, MOTHER_OFFSET_Y } = CANVAS_CONFIG;
    const textBySlug = {};
    for (const n of nodes) {
        if (n.type !== 'text') continue;
        const s = slugOfNode(n);
        if (s) textBySlug[s] = n;
    }
    const fitted = [];
    for (const group of nodes.filter(n => n.type === 'group')) {
        const pSlug = slugOfNode(group);
        const members = ((pSlug && membersByParent[pSlug]) || []).map(s => textBySlug[s]).filter(Boolean);
        if (members.length < 2) continue;
        const gx = Math.min(...members.map(n => n.x)) - PADDING_X;
        const gy = Math.min(...members.map(n => n.y)) - PADDING_Y;
        const gw = Math.max(...members.map(n => n.x + n.width)) - gx + PADDING_X;
        const gh = Math.max(...members.map(n => n.y + n.height)) - gy + PADDING_X;
        if (group.x === gx && group.y === gy && group.width === gw && group.height === gh) continue;
        group.x = gx; group.y = gy; group.width = gw; group.height = gh;
        fitted.push(pSlug);
        const parent = textBySlug[pSlug];
        if (parent && String(parent.text || '').includes('`#big`')) {
            parent.width = BIG_CARD_W;
            parent.height = BIG_CARD_H;
            parent.x = gx + gw / 2 - BIG_CARD_W / 2;
            parent.y = gy - BIG_CARD_H - MOTHER_OFFSET_Y;
        }
    }
    return fitted.length ? { data: out, fitted } : null;
};

// Dao parentMap { slugCon: Set|Array<slugCha> } -> { slugCha: [slugCon, ...] }
const buildMembersByParent = (parentMap) => {
    const out = {};
    for (const [child, parents] of Object.entries(parentMap || {})) {
        for (const p of parents || []) (out[p] = out[p] || []).push(child);
    }
    return out;
};

module.exports = class FactoryCanvasPlugin extends Plugin {
    async onload() {
        console.log('[FactoryCanvas] Plugin loaded: Smooth & Jitter-Free Canvas Controller.');
        
        let canvasSyncDebounceTimer = null;
        let isInternalUpdating = false;
        let lastSyncTriggeredAt = 0;
        let lastPluginWriteTime = 0; // Time-lock 1500ms dập tắt vòng lặp đệ quy cascade lưu đĩa

        // --- UNDO/REDO SUPPRESSION STATE ---
        // Khi user Ctrl+Z/Y, bat co de tam hoan automation trong 1500ms
        // Sau timeout, chay reconcile nhe (chi sync FM va AutoFit, khong re-arrange)
        let isUndoRedoing = false;
        let undoDebounceTimer = null;
        let previousDirectEdges = {}; // slug_con -> slug_cha (theo doi canh truc tiep de bat Undo/Delete chinh xac 100%)

        // --- MEMBER FIT & CANVAS SYNC SCHEDULER STATE ---
        let isCanvasSyncRunning = false;     // chong 2 lan sync canvas chay chong nhau
        let pendingCanvasFile = null;        // file canvas cua su kien modify gan nhat (dung khi sync bi hoan)
        let lastUndoAt = 0;                  // thoi diem Ctrl+Z/Y gan nhat: Member Fit tam dung 1500ms de reconcile Undo chay truoc
        let memberFitTimer = null;
        const fitHookedEls = new WeakSet();  // containerEl da gan hook pointerup trong lan load plugin nay

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
        // NHÓM 2.5: LIVE RAM CANVAS EXTRACTOR & STRUCTURED LOGGER
        // -------------------------------------------------------------
        const logFC = (module, message, data = null) => {
            const prefix = `[FactoryCanvas][${module}]`;
            if (data !== null) {
                console.log(`${prefix} ${message}`, data);
            } else {
                console.log(`${prefix} ${message}`);
            }
        };

        const getLiveCanvasData = async (canvasObj, canvasFile) => {
            if (canvasObj) {
                if (typeof canvasObj.exportData === 'function') {
                    return canvasObj.exportData();
                }
                if (canvasObj.nodes && canvasObj.edges) {
                    const nodes = Array.from(canvasObj.nodes.values()).map(n => ({
                        id: n.id,
                        type: n.type || (n.text !== undefined ? 'text' : (n.label !== undefined ? 'group' : 'file')),
                        x: n.x,
                        y: n.y,
                        width: n.width,
                        height: n.height,
                        text: n.text,
                        label: n.label,
                        color: n.color
                    }));
                    const edges = Array.from(canvasObj.edges.values()).map(e => ({
                        id: e.id,
                        fromNode: e.from?.node?.id,
                        fromSide: e.from?.side,
                        toNode: e.to?.node?.id,
                        toSide: e.to?.side,
                        color: e.color
                    }));
                    return { nodes, edges };
                }
            }
            if (canvasFile) {
                const raw = await this.app.vault.read(canvasFile);
                return JSON.parse(raw);
            }
            return null;
        };


        // Lay leaf dang mo audience-hierarchy.canvas (null neu chua mo)
        const getAudienceCanvasLeaf = () => this.app.workspace.getLeavesOfType('canvas')
            .find(l => l.view?.file?.path?.includes('audience-hierarchy')) || null;

        // Ghi canvas RAM xuong dia NGAY (neu dang dirty) TRUOC khi ghi Frontmatter,
        // de renderer Python (chay sau khi md doi) doc dung trang thai hien tai, khong ghi de.
        const flushCanvasToDisk = async () => {
            const view = getAudienceCanvasLeaf()?.view;
            if (!view || !view.dirty || typeof view.saveImmediately !== 'function') return;
            lastPluginWriteTime = Date.now(); // chan vault.on('modify') do chinh plugin ghi
            try {
                await view.saveImmediately();
            } catch (e) {
                console.warn('[FactoryCanvas] flushCanvasToDisk error:', e);
            }
        };

        // MEMBER FIT: Group cua moi cha om tron cac the con (theo FM) tai vi tri hien tai.
        // getData -> compute -> importData chay dong bo trong 1 tick: khong lech voi RAM.
        const applyGroupFit = (canvas, membersByParent, reason) => {
            const res = computeGroupFit(canvas.getData(), membersByParent);
            if (!res) return false;
            canvas.importData(res.data, true);
            logFC('FIT', `${reason}: Group của [${res.fitted.join(', ')}] co giãn ôm thẻ con.`);
            return true;
        };

        // Goi 400ms sau pointerup (sau khi Obsidian push history 250ms) -> overrideHistory gop vao buoc Undo cua thao tac keo.
        // Tam dung khi dang Undo/Redo: reconcile Undo phai doc vi tri the TRUOC khi Group bi co gian.
        const fitGroupsInRam = async () => {
            const isBlocked = () => isUndoRedoing || isInternalUpdating || (Date.now() - lastUndoAt < 1500);
            if (isBlocked()) return;
            const canvas = getAudienceCanvasLeaf()?.view?.canvas;
            if (!canvas || typeof canvas.getData !== 'function' || typeof canvas.importData !== 'function') return;
            const vaultParentMap = await getVaultParentMap();
            if (isBlocked()) return; // kiem tra lai sau await (user co the vua Ctrl+Z)
            if (applyGroupFit(canvas, buildMembersByParent(vaultParentMap), 'pointerup')) {
                if (typeof canvas.overrideHistory === 'function') canvas.overrideHistory();
                if (typeof canvas.requestFrame === 'function') canvas.requestFrame();
            }
        };



        // -------------------------------------------------------------
        // NHÓM 5: SILENT ORIGIN-SIDE REVERSE-SYNC (ĐỒNG BỘ NGẦM)
        // -------------------------------------------------------------
        const syncCanvasToVault = async (canvasData, canvasFilePath, skipRearrange = false) => {
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

            const audienceNodes = textNodes.filter(n => n.slug);

            // 1. Khoi tao danh sach va tap hop canh tu Canvas
            const vaultParentMap = await getVaultParentMap();
            const nextStepMap = {};
            for (const tn of audienceNodes) {
                nextStepMap[tn.slug] = new Set();
            }

            const activeDirectEdges = {}; // slug_con -> slug_cha (Mui ten day tro truc tiep vao the con)
            const directEdgeInfo = {}; // slug_con -> { edgeId, childId, parentSlug } phuc vu Smart Snap
            const activeGroupParents = new Set(); // slug_cha (Mui ten day tro vao Khung Group)
            let canvasColorModified = false;

            for (const edge of edges) {
                const fromNode = nodeById[edge.fromNode];
                const toNode = nodeById[edge.toNode];
                if (!fromNode || !toNode) continue;

                const fromSide = edge.fromSide || 'right';

                // QUY TAC 1: Xuat phat tu canh duoi (bottom) -> QUAN HE ME-CON (PHA HE)
                if (fromSide === 'bottom') {
                    if (!edge.color) {
                        edge.color = CANVAS_CONFIG.COLOR_EDGE_PHA_HE;
                        canvasColorModified = true;
                    }
                    const fromSlug = extractSlug(fromNode.text || fromNode.label);
                    if (!fromSlug) continue;

                    // A. Mui ten tro TRUC TIEP vao 1 The Text Node con
                    if (toNode.type === 'text' && toNode.slug) {
                        if (fromSlug !== toNode.slug) {
                            activeDirectEdges[toNode.slug] = fromSlug;
                            directEdgeInfo[toNode.slug] = { edgeId: edge.id, childId: toNode.id, parentSlug: fromSlug };
                            logFC('SYNC', `Phát hiện cạnh phả hệ: [${fromSlug}] -> [${toNode.slug}]`);
                        }
                    }
                    // B. Mui ten tro vao Khung Group -> Ghi nhan Cha dang ket noi pha he voi nhom
                    // (TUYET DOI khong dung toa do Bounding Box de phong doan/gan thanh vien)
                    else if (toNode.type === 'group') {
                        activeGroupParents.add(fromSlug);
                    }
                } 
                // QUY TAC 2: Xuat phat tu canh ben (right/left) -> QUAN HE JOB STEP
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

            const groupNodes = nodes.filter(n => n.type === 'group');

            // 2. Xay dung parentMap ket hop Direct Edge Tracking & Spatial Group Preservation
            const parentMap = {};
            for (const tn of audienceNodes) {
                const slug = tn.slug;
                if (activeDirectEdges[slug]) {
                    parentMap[slug] = new Set([activeDirectEdges[slug]]);
                    logFC('SYNC', `Thẻ [${slug}] nhận cha trực tiếp từ mũi tên: [${activeDirectEdges[slug]}]`);
                } else {
                    // Thẻ không có mũi tên trực tiếp: giữ cha p nếu p có Group và có mũi tên p->Group.
                    // Thao tác trực tiếp: VỊ TRÍ KHÔNG quyết định quan hệ (kéo thẻ ra ngoài -> Group nở ra ôm thẻ, Member Fit).
                    // Undo/Redo (skipRearrange): vẫn yêu cầu thẻ nằm trong Group để gỡ quan hệ khi hoàn tác nối edge + Smart Snap.
                    const currentParents = vaultParentMap[slug] || new Set();
                    const retainedParents = new Set();
                    for (const p of currentParents) {
                        const groupForP = groupNodes.find(g => extractSlug(g.label) === p);
                        const isInsideGroupOfP = groupForP && (
                            tn.x >= (groupForP.x - 30) &&
                            (tn.x + (tn.width || CANVAS_CONFIG.CARD_W)) <= (groupForP.x + groupForP.width + 30) &&
                            tn.y >= (groupForP.y - 30) &&
                            (tn.y + (tn.height || CANVAS_CONFIG.CARD_H)) <= (groupForP.y + groupForP.height + 30)
                        );

                        const hasGroupLink = Boolean(groupForP) && activeGroupParents.has(p);
                        const keep = skipRearrange ? (hasGroupLink && isInsideGroupOfP) : hasGroupLink;
                        if (keep) {
                            retainedParents.add(p);
                        } else {
                            logFC('SYNC', `Xóa quan hệ phả hệ [${p}] khỏi thẻ [${slug}] (không có mũi tên trực tiếp/mũi tên vào Group${skipRearrange ? ' hoặc nằm ngoài Group sau Undo/Redo' : ''}).`);
                        }
                    }
                    parentMap[slug] = retainedParents;
                }
            }

            // Cap nhat lai bo nho dem mui ten truc tiep cho lan sync tiep theo
            previousDirectEdges = { ...activeDirectEdges };

            // Tô màu xanh phả hệ trực tiếp trong RAM Canvas và re-render tức thì
            if (canvasColorModified) {
                try {
                    const leaves = this.app.workspace.getLeavesOfType('canvas');
                    for (const leaf of leaves) {
                        const canvasObj = leaf.view?.canvas;
                        if (canvasObj && canvasObj.edges) {
                            for (const [, edgeInst] of canvasObj.edges) {
                                if (edgeInst.from?.side === 'bottom') {
                                    const targetColor = CANVAS_CONFIG.COLOR_EDGE_PHA_HE;
                                    if (!edgeInst.color || edgeInst.color !== targetColor) {
                                        if (typeof edgeInst.setColor === 'function') {
                                            edgeInst.setColor(targetColor);
                                        } else {
                                            edgeInst.color = targetColor;
                                            if (typeof edgeInst.render === 'function') edgeInst.render();
                                        }
                                    }
                                }
                            }
                        }
                    }
                } catch (e) {
                    console.warn('[FactoryCanvas] Error updating edge colors in RAM:', e);
                }
            }

            // 2.5 SMART SNAP: the vua duoc noi cha (thao tac truc tiep, KHONG ap dung cho Undo/Redo)
            // duoc xep vao o trong ke tiep trong Group cua cha. Ap trong RAM + overrideHistory
            // de gop vao chinh buoc Undo cua thao tac noi edge (1 lan Ctrl+Z hoan tac tat ca).
            if (!skipRearrange && Date.now() - lastUndoAt >= 1500) {
                const snapCanvas = getAudienceCanvasLeaf()?.view?.canvas;
                if (snapCanvas && typeof snapCanvas.getData === 'function' && typeof snapCanvas.importData === 'function') {
                    let snappedCount = 0;
                    for (const [childSlug, info] of Object.entries(directEdgeInfo)) {
                        const pSlug = activeDirectEdges[childSlug];
                        if (!pSlug || pSlug !== info.parentSlug) continue;
                        // Frontmatter da co cha nay -> khong phai thao tac moi (vd: vua reload plugin) -> khong snap
                        if (vaultParentMap[childSlug] && vaultParentMap[childSlug].has(pSlug)) continue;
                        const result = computeGroupSnap(snapCanvas.getData(), info.childId, pSlug, info.edgeId);
                        if (!result) continue; // Cha chua co Group -> giu nguyen vi tri the (TC-11)
                        snapCanvas.importData(result.data, true);
                        snappedCount++;
                        logFC('SNAP', `Xếp [${childSlug}] vào Group của [${pSlug}] (ô ${result.slot}, đẩy tầng dưới ${result.shiftY}px).`);
                    }
                    // Member Fit du phong (thao tac khong qua pointerup, vd: phim mui ten): Group om the con theo quan he sau sync
                    const fitted = applyGroupFit(snapCanvas, buildMembersByParent(parentMap), 'sync');
                    if (snappedCount > 0 || fitted) {
                        if (typeof snapCanvas.overrideHistory === 'function') snapCanvas.overrideHistory();
                        if (typeof snapCanvas.requestFrame === 'function') snapCanvas.requestFrame();
                    }
                }
            }

            // 2.6 FLUSH: ghi canvas RAM xuong dia TRUOC khi ghi Frontmatter (ap dung ca Undo/Redo),
            // tranh renderer Python doc canvas cu roi ghi de trang thai vua thay doi.
            await flushCanvasToDisk();

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
                            logFC('SYNC', `Cập nhật Frontmatter [${file.basename}] -> parent_audience:`, desiredParents);
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
                lastPluginWriteTime = Date.now();
                lastSyncTriggeredAt = Date.now();
                new Notice(`[Factory Canvas] 🔄 Đã đồng bộ quan hệ vào ${updatedCount} file Audience`, 2500);
                // TUYET DOI KHONG tu dong goi reArrangeCanvasLayout tai day.
                // Re-arrange chi duoc phep chay khi nguoi dung chu dong click nut '1-Click Re-arrange' hoac menu chuot phai.
                // Viec tu dong re-arrange se ghi de file canvas, lam XOA SACH Undo history trong RAM va nuot the con vao group.
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

            const audienceNodes = textNodes.filter(n => {
                n.slug = extractSlug(n.text);
                return Boolean(n.slug);
            });

            const CARD_W = CANVAS_CONFIG.CARD_W;
            const CARD_H = CANVAS_CONFIG.CARD_H;
            const GAP_X = CANVAS_CONFIG.GAP_X;
            const GAP_Y = CANVAS_CONFIG.GAP_Y;
            const COLS = CANVAS_CONFIG.COLS;
            const START_X = CANVAS_CONFIG.START_X;
            const START_Y = CANVAS_CONFIG.START_Y;

            const vaultParentMap = await getVaultParentMap();

            // Tìm Root Node: Thẻ có slug không có parent trong Frontmatter và có con, hoặc thẻ đầu tiên không có parent
            let rootNode = audienceNodes.find(n => {
                const pSet = vaultParentMap[n.slug];
                return (!pSet || pSet.size === 0) && (n.color === CANVAS_CONFIG.COLOR_ROOT || (n.text && n.text.includes('#big')));
            });
            if (!rootNode) {
                rootNode = audienceNodes.find(n => !vaultParentMap[n.slug] || vaultParentMap[n.slug].size === 0);
            }
            const rootSlug = rootNode ? rootNode.slug : null;

            // Danh sách thẻ con cấp dưới
            const childNodes = audienceNodes.filter(n => n !== rootNode);

            // 1. Phân nhóm thẻ theo Cây Phả Hệ thực tế trong Frontmatter
            const nodesByParent = {};
            const unlinkedNodes = [];

            for (const node of childNodes) {
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

            // Thẻ thuộc Level 1 (con trực tiếp của Root)
            let level1Nodes = (rootSlug && nodesByParent[rootSlug]) ? nodesByParent[rootSlug] : [];
            if (level1Nodes.length === 0 && !rootSlug) {
                level1Nodes = childNodes.filter(n => !unlinkedNodes.includes(n));
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

            // 3. Tính Bounding Box Group 1 & Căn Root Audience ở ĐƯỜNG CHÍNH TRỰC
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
                return ps === rootSlug;
            });

            if (mainGroupNode) {
                mainGroupNode.x = l1_minX - CANVAS_CONFIG.PADDING_X;
                mainGroupNode.y = l1_minY - CANVAS_CONFIG.PADDING_Y;
                mainGroupNode.width = l1_groupW;
                mainGroupNode.height = l1_groupH;
            }

            if (rootNode) {
                rootNode.width = CANVAS_CONFIG.ROOT_CARD_W || CANVAS_CONFIG.BIG_CARD_W;
                rootNode.height = CANVAS_CONFIG.ROOT_CARD_H || CANVAS_CONFIG.BIG_CARD_H;
                rootNode.x = l1_centerX - rootNode.width / 2;
                rootNode.y = (l1_minY - CANVAS_CONFIG.PADDING_Y) - rootNode.height - CANVAS_CONFIG.MOTHER_OFFSET_Y;
            }

            // 4. Bố trí các Khung Group Level 2+ (Tầng dưới, căn chính trực theo thẻ cha)
            let currentTierY = (l1_minY - CANVAS_CONFIG.PADDING_Y) + l1_groupH + CANVAS_CONFIG.TIER_GAP;

            for (const [pSlug, children] of Object.entries(nodesByParent)) {
                if (pSlug === rootSlug || children.length === 0) continue;

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
                const subGroupLabel = subGroupNode && subGroupNode.label.includes(`[[${pSlug}]]`)
                    ? subGroupNode.label
                    : `📦 NHÓM CON: [[${pSlug}]]`;

                if (!subGroupNode && children.length > 1) {
                    subGroupNode = {
                        id: `group_sub_${pSlug}`,
                        type: "group",
                        label: subGroupLabel,
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
                    subGroupNode.label = subGroupLabel;
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

            // A. Mũi tên Phả hệ Root Audience -> Group 1 (hoặc thẻ con đơn lẻ)
            if (rootNode) {
                if (level1Nodes.length > 1 && mainGroupNode) {
                    const pairKey = `${rootNode.id}->${mainGroupNode.id}`;
                    newEdges.push({
                        id: "edge_root_to_group",
                        fromNode: rootNode.id,
                        fromSide: "bottom",
                        toNode: mainGroupNode.id,
                        toSide: "top",
                        color: userColorMap[pairKey] || CANVAS_CONFIG.COLOR_EDGE_PHẢ_HỆ
                    });
                } else if (level1Nodes.length === 1) {
                    const singleChildId = nodeIdBySlug[level1Nodes[0].slug];
                    if (singleChildId) {
                        const pairKey = `${rootNode.id}->${singleChildId}`;
                        newEdges.push({
                            id: "edge_root_to_single_child",
                            fromNode: rootNode.id,
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
                if (pSlug === rootSlug || children.length === 0) continue;
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

            // Cập nhật lại previousDirectEdges theo các cạnh mới được sinh ra
            const updatedDirectEdges = {};
            for (const ne of newEdges) {
                if (ne.fromSide === 'bottom') {
                    const toNodeObj = textNodes.find(n => n.id === ne.toNode);
                    const fromNodeObj = textNodes.find(n => n.id === ne.fromNode);
                    if (toNodeObj && toNodeObj.slug && fromNodeObj && fromNodeObj.slug) {
                        updatedDirectEdges[toNodeObj.slug] = fromNodeObj.slug;
                    }
                }
            }
            previousDirectEdges = updatedDirectEdges;

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
        // NHÓM 6.5: AUTO-CENTER VIEWPORT CONTROLLER & FLYOUT TRIGGER
        // -------------------------------------------------------------
        const getCanvasDiagramBBox = (canvasObj) => {
            if (!canvasObj || !canvasObj.nodes || canvasObj.nodes.size === 0) return null;
            let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
            for (const [, node] of canvasObj.nodes) {
                const nx = node.x ?? 0;
                const ny = node.y ?? 0;
                const nw = node.width ?? 0;
                const nh = node.height ?? 0;
                if (nx < minX) minX = nx;
                if (ny < minY) minY = ny;
                if (nx + nw > maxX) maxX = nx + nw;
                if (ny + nh > maxY) maxY = ny + nh;
            }
            if (minX === Infinity) return null;
            return {
                minX, minY, maxX, maxY,
                width: Math.max(1, maxX - minX),
                height: Math.max(1, maxY - minY),
                cx: (minX + maxX) / 2,
                cy: (minY + maxY) / 2
            };
        };

        const centerCanvasDiagram = (canvasObj) => {
            if (!canvasObj) return;
            const bbox = getCanvasDiagramBBox(canvasObj);
            if (!bbox) {
                new Notice('⚠️ Không tìm thấy đối tượng nào trên Canvas để căn giữa.', 2500);
                return;
            }

            if (typeof canvasObj.panTo === 'function') {
                canvasObj.panTo(bbox.cx, bbox.cy);
            } else if (typeof canvasObj.panToCoord === 'function') {
                canvasObj.panToCoord({ x: bbox.cx, y: bbox.cy });
            } else {
                const container = canvasObj.containerEl || canvasObj.wrapperEl || canvasObj.view?.containerEl;
                const vpW = container ? container.clientWidth : (window.innerWidth || 1200);
                const vpH = container ? container.clientHeight : (window.innerHeight || 800);
                const currentZoom = canvasObj.zoom || 1.0;
                canvasObj.tx = (vpW / 2) - (bbox.cx * currentZoom);
                canvasObj.ty = (vpH / 2) - (bbox.cy * currentZoom);
                if (typeof canvasObj.requestFrame === 'function') canvasObj.requestFrame();
            }
            new Notice('🎯 [Factory Canvas] Đã đưa trọng tâm sơ đồ về chính giữa màn hình!', 2000);
        };

        const isZoomToFitButton = (el) => {
            if (!el) return null;
            const btn = el.closest('.canvas-control-item');
            if (!btn) return null;

            // 1. Kiểm tra aria-label của nút
            const label = (btn.getAttribute('aria-label') || '').toLowerCase();
            if (label.includes('fit') || label.includes('vừa') || label.includes('khung') || label.includes('zoom to fit')) {
                return btn;
            }

            // 2. Kiểm tra class của Icon SVG
            if (btn.querySelector('svg.lucide-maximize, svg.lucide-maximize-2, svg.lucide-expand, svg.lucide-focus, svg.lucide-scan, svg.lucide-shrink, [data-icon*="maximize"]')) {
                return btn;
            }

            // 3. Fallback: Dò vị trí nút trong Control Group chứa Zoom
            const group = btn.closest('.canvas-control-group');
            if (group && group.querySelector('.lucide-plus, .lucide-minus, [aria-label*="zoom" i], [aria-label*="phóng" i], [aria-label*="thu" i]')) {
                const items = Array.from(group.querySelectorAll('.canvas-control-item'));
                // Nếu nhóm có 4 nút: [0: Zoom In, 1: Reset, 2: Zoom to Fit, 3: Zoom Out]
                if (items.length >= 4 && items[2] === btn) {
                    return btn;
                }
                // Nếu nhóm có 3 nút: [0: Zoom In, 1: Zoom to Fit, 2: Zoom Out]
                if (items.length === 3 && items[1] === btn) {
                    return btn;
                }
            }
            return null;
        };

        const showAutoCenterFlyout = (anchorBtn, containerEl, canvasObj) => {
            // 1. Dọn dẹp flyout cũ nếu đang mở
            document.querySelectorAll('.factory-autocenter-flyout').forEach(el => el.remove());
            if (!anchorBtn || !containerEl) return;

            const btnRect = anchorBtn.getBoundingClientRect();
            const containerRect = containerEl.getBoundingClientRect();

            // 2. Tạo phần tử Flyout
            const flyout = document.createElement('div');
            flyout.className = 'factory-autocenter-flyout clickable-icon canvas-control-item';
            flyout.setAttribute('aria-label', '🎯 Auto-Center sơ đồ (Click chuột phải để chọn)');
            
            // Đặt vị trí bên trái nút Zoom to Fit (gắn trực tiếp vào containerEl để tránh overflow: hidden)
            const topOffset = btnRect.top - containerRect.top + (btnRect.height - 30) / 2;
            const leftOffset = btnRect.left - containerRect.left - 38;

            flyout.style.position = 'absolute';
            flyout.style.top = `${topOffset}px`;
            flyout.style.left = `${leftOffset}px`;
            flyout.style.width = '30px';
            flyout.style.height = '30px';
            flyout.style.display = 'flex';
            flyout.style.alignItems = 'center';
            flyout.style.justifyContent = 'center';
            flyout.style.zIndex = '9999';
            flyout.style.boxShadow = '0 3px 10px rgba(0, 0, 0, 0.35)';
            flyout.style.borderRadius = 'var(--radius-s, 4px)';
            flyout.style.background = 'var(--background-secondary, #202020)';
            flyout.style.border = '1px solid var(--background-modifier-border, #444)';
            flyout.style.cursor = 'pointer';
            flyout.style.transition = 'transform 0.12s ease, opacity 0.12s ease';
            flyout.style.transform = 'scale(0.85)';
            flyout.style.opacity = '0';

            if (typeof setIcon === 'function') {
                setIcon(flyout, 'crosshair');
            } else {
                flyout.textContent = '🎯';
            }

            containerEl.appendChild(flyout);

            // Animation xuất hiện mượt mà
            requestAnimationFrame(() => {
                flyout.style.transform = 'scale(1)';
                flyout.style.opacity = '1';
            });

            const triggerAutoCenter = (e) => {
                e.preventDefault();
                e.stopPropagation();
                if (canvasObj) {
                    centerCanvasDiagram(canvasObj);
                }
                flyout.remove();
                cleanupListeners();
            };

            // Bắt sự kiện Click Chuột Phải hoặc Chuột Trái để chọn Auto-Center
            flyout.addEventListener('contextmenu', triggerAutoCenter);
            flyout.addEventListener('click', triggerAutoCenter);

            // 3. Tự động đóng khi click ra ngoài
            const onOutsideClick = (e) => {
                if (!flyout.contains(e.target) && !anchorBtn.contains(e.target)) {
                    flyout.remove();
                    cleanupListeners();
                }
            };

            const cleanupListeners = () => {
                document.removeEventListener('pointerdown', onOutsideClick);
                document.removeEventListener('contextmenu', onOutsideClick);
            };

            setTimeout(() => {
                document.addEventListener('pointerdown', onOutsideClick);
                document.addEventListener('contextmenu', onOutsideClick);
            }, 60);
        };

        const attachCanvasControlsRightClickHook = (leaf) => {
            if (!leaf?.view) return;
            const containerEl = leaf.view.containerEl;
            if (!containerEl || containerEl._hasFactoryFlyoutHook) return;
            containerEl._hasFactoryFlyoutHook = true;

            // Sử dụng Event Capture trên containerEl để bắt contextmenu trước các lớp xử lý của Canvas
            containerEl.addEventListener('contextmenu', (evt) => {
                const zoomToFitBtn = isZoomToFitButton(evt.target);
                if (zoomToFitBtn) {
                    evt.preventDefault();
                    evt.stopPropagation();
                    showAutoCenterFlyout(zoomToFitBtn, containerEl, leaf.view.canvas);
                }
            }, true);
        };

        const cleanupFloatingInjections = () => {
            try {
                document.querySelectorAll('.factory-zoom-badge, .factory-autocenter-control, .factory-autocenter-flyout').forEach(el => el.remove());
            } catch (e) {}
        };

        // -------------------------------------------------------------
        // NHÓM 7: ĐĂNG KÝ CÁC ĐIỂM TRUY CẬP (CANVAS HEADER & COMMAND & CONTEXT MENU)
        // -------------------------------------------------------------
        
        // 1. Command Palette (Ctrl + P)
        this.addCommand({
            id: 'auto-center-audience-canvas',
            name: '🎯 Đưa sơ đồ về chính giữa màn hình (Auto-Center)',
            callback: () => {
                const leaves = this.app.workspace.getLeavesOfType('canvas');
                for (const leaf of leaves) {
                    if (leaf.view?.canvas) {
                        centerCanvasDiagram(leaf.view.canvas);
                        return;
                    }
                }
            }
        });

        this.addCommand({
            id: 'rearrange-audience-canvas',
            name: '🪄 Căn chỉnh lại toàn bộ sơ đồ Audience Canvas (Re-arrange Layout)',
            callback: async () => {
                await reArrangeCanvasLayout(true);
            }
        });

        // 2. Canvas View Header Action Buttons & Zoom to fit Right-click hook
        const syncCanvasControlsUI = () => {
            cleanupFloatingInjections();
            const leaves = this.app.workspace.getLeavesOfType('canvas');
            for (const leaf of leaves) {
                if (!leaf.view) continue;

                // 2.1. Nút Re-arrange Layout trên Header (sparkles)
                if (!leaf.view._hasFactoryRearrangeBtn) {
                    leaf.view._hasFactoryRearrangeBtn = true;
                    if (typeof leaf.view.addAction === 'function') {
                        leaf.view.addAction('sparkles', 'Căn chỉnh sơ đồ Canvas (Re-arrange)', async () => {
                            await reArrangeCanvasLayout(true);
                        });
                    }
                }

                // 2.2. Gắn Hook Chuột Phải qua Capture Listener trên Canvas Container
                attachCanvasControlsRightClickHook(leaf);
            }
        };

        this.registerEvent(this.app.workspace.on('layout-change', syncCanvasControlsUI));
        this.registerEvent(this.app.workspace.on('active-leaf-change', syncCanvasControlsUI));
        syncCanvasControlsUI();
        setTimeout(syncCanvasControlsUI, 500);

        // -------------------------------------------------------------
        // NHOM 7.5: UNDO/REDO DETECTION & RECONCILE ENGINE
        // Phat hien Ctrl+Z/Y va nut Undo/Redo tren Toolbar
        // Hoan automation trong 1500ms, sau do reconcile Frontmatter nhe
        // -------------------------------------------------------------

        const reconcileAfterUndo = async () => {
            try {
                const leaves = this.app.workspace.getLeavesOfType('canvas');
                const targetLeaf = leaves.find(l => l.view?.file?.path?.includes('audience-hierarchy'));
                if (!targetLeaf?.view?.file) return;

                const canvasFile = targetLeaf.view.file;
                const canvasObj = targetLeaf.view?.canvas;

                // Uu tien lay du lieu LIVE truc tiep tu Canvas RAM ngay sau Undo
                // Tranh doc tu dia vi Obsidian debounce ghi dia khien du lieu bi cu/stale
                logFC('UNDO', 'Bắt đầu reconcile sau thao tác Undo/Redo...');
                const canvasData = await getLiveCanvasData(canvasObj, canvasFile);

                // Goi syncCanvasToVault de reconcile Frontmatter ngay lap tuc
                await syncCanvasToVault(canvasData, canvasFile.path, true);
            } catch (e) {
                console.warn('[FactoryCanvas] reconcileAfterUndo error:', e);
            }
        };

        const triggerUndoSuppress = () => {
            isUndoRedoing = true;
            lastUndoAt = Date.now();
            clearTimeout(memberFitTimer);
            clearTimeout(canvasSyncDebounceTimer);
            // Phản hồi nhanh sau 400ms để người dùng thấy Frontmatter xóa ngay sau Undo
            undoDebounceTimer = setTimeout(() => {
                isUndoRedoing = false;
                reconcileAfterUndo();
            }, 400);
        };

        // Keyboard Listener: Ctrl+Z / Ctrl+Shift+Z / Ctrl+Y
        this._onCanvasKeydown = (evt) => {
            if (!evt.ctrlKey && !evt.metaKey) return;
            if (evt.key === 'z' || evt.key === 'Z' || evt.key === 'y' || evt.key === 'Y') {
                const leaves = this.app.workspace.getLeavesOfType('canvas');
                const hasAudienceCanvas = leaves.some(l => l.view?.file?.path?.includes('audience-hierarchy'));
                if (hasAudienceCanvas) {
                    triggerUndoSuppress();
                }
            }
        };
        document.addEventListener('keydown', this._onCanvasKeydown, true);

        // Toolbar Listener: Nut Undo/Redo tren thanh cong cu Canvas
        const attachUndoRedoToolbarHook = (leaf) => {
            if (!leaf?.view?.containerEl) return;
            const containerEl = leaf.view.containerEl;
            if (containerEl._hasFactoryUndoHook) return;
            containerEl._hasFactoryUndoHook = true;

            containerEl.addEventListener('click', (evt) => {
                const btn = evt.target.closest('.canvas-control-item');
                if (!btn) return;
                const label = (btn.getAttribute('aria-label') || '').toLowerCase();
                if (label.includes('undo') || label.includes('redo') ||
                    label.includes('hoàn tác') || label.includes('làm lại') ||
                    label.includes('hoan tac') || label.includes('lam lai')) {
                    if (leaf.view?.file?.path?.includes('audience-hierarchy')) {
                        triggerUndoSuppress();
                    }
                }
            }, true);
        };

        // MEMBER FIT HOOK: user tha chuot tren canvas (keo the, keo canh...) -> 400ms sau co gian Group om the con.
        // registerDomEvent tu go listener khi unload plugin (khong tich luy qua cac lan reload - TC-10).
        const attachMemberFitHook = (leaf) => {
            const containerEl = leaf?.view?.containerEl;
            if (!containerEl || fitHookedEls.has(containerEl)) return;
            fitHookedEls.add(containerEl);
            this.registerDomEvent(containerEl, 'pointerup', (evt) => {
                if (!leaf.view?.file?.path?.includes('audience-hierarchy')) return;
                const t = evt.target;
                if (t && typeof t.closest === 'function' &&
                    t.closest('.canvas-controls, .canvas-control-item, .menu, .factory-autocenter-control, .factory-autocenter-flyout')) return;
                clearTimeout(memberFitTimer);
                memberFitTimer = setTimeout(() => { fitGroupsInRam(); }, 400);
            }, true);
        };

        const syncUndoHooks = () => {
            const leaves = this.app.workspace.getLeavesOfType('canvas');
            for (const leaf of leaves) {
                attachUndoRedoToolbarHook(leaf);
                attachMemberFitHook(leaf);
            }
        };
        this.registerEvent(this.app.workspace.on('layout-change', syncUndoHooks));
        this.registerEvent(this.app.workspace.on('active-leaf-change', syncUndoHooks));
        syncUndoHooks();

        // 3. Right-Click Context Menu trên Canvas
        this.registerEvent(
            this.app.workspace.on('canvas:menu', (menu, canvas) => {
                menu.addItem((item) => {
                    item.setTitle('🎯 Đưa sơ đồ về giữa (Auto-Center)')
                        .setIcon('crosshair')
                        .onClick(() => {
                            centerCanvasDiagram(canvas);
                        });
                });
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
            // Khi file Audience Markdown bị sửa, Frontmatter đã lưu quan hệ phả hệ.
            // KHÔNG co giãn/sắp xếp Group tại đây: renderer Python vẽ lại canvas theo FM; Member Fit chỉ chạy theo thao tác trên canvas.
            return;
        };

        // CANVAS SYNC SCHEDULER: su kien canvas KHONG BAO GIO bi bo.
        // Dang time-lock 1500ms sau lan plugin ghi / dang co sync khac chay -> hoan lai, khong return.
        // syncCanvasToVault idempotent (khong ghi khi khong doi) nen hoan lai khong tao vong lap.
        const scheduleCanvasSync = (delayMs) => {
            clearTimeout(canvasSyncDebounceTimer);
            canvasSyncDebounceTimer = setTimeout(runCanvasSync, delayMs);
        };

        const runCanvasSync = async () => {
            if (isUndoRedoing || !pendingCanvasFile) return; // reconcileAfterUndo se doc RAM va dong bo
            const lockLeft = lastPluginWriteTime + 1500 - Date.now();
            if (isCanvasSyncRunning || isInternalUpdating || lockLeft > 0) {
                scheduleCanvasSync(Math.max(300, lockLeft + 50));
                return;
            }
            isCanvasSyncRunning = true;
            try {
                const file = pendingCanvasFile;
                const canvasObj = getAudienceCanvasLeaf()?.view?.canvas;
                const canvasData = await getLiveCanvasData(canvasObj, file);
                await syncCanvasToVault(canvasData, file.path);
            } catch (e) {
                console.error('[FactoryCanvas] Error handling canvas modify:', e);
            } finally {
                isCanvasSyncRunning = false;
            }
        };

        this.registerEvent(
            this.app.vault.on('modify', async (file) => {
                // 1. Khi file Canvas bị sửa (user, Obsidian autosave, renderer)
                if (file.extension === 'canvas' && file.path.includes('audience-hierarchy')) {
                    if (isUndoRedoing) return;
                    pendingCanvasFile = file;
                    scheduleCanvasSync(300);
                }
                // 2. Khi file Audience Markdown bị sửa frontmatter ngoài Canvas
                else if (file.extension === 'md' && file.path.startsWith('01-Atomic/Audiences')) {
                    await handleAudienceMdChange();
                }
            })
        );

        this.registerEvent(
            this.app.metadataCache.on('changed', async (file) => {
                if (isUndoRedoing) return;
                if (file.path.startsWith('01-Atomic/Audiences')) {
                    await handleAudienceMdChange();
                }
            })
        );
    }

    onunload() {
        console.log('[FactoryCanvas] Plugin unloaded.');
        try {
            document.querySelectorAll('.factory-zoom-badge, .factory-autocenter-control, .factory-autocenter-flyout').forEach(el => el.remove());
        } catch (e) {}
        if (this._onCanvasKeydown) {
            document.removeEventListener('keydown', this._onCanvasKeydown, true);
            this._onCanvasKeydown = null;
        }
    }
};

// Export ham thuan de kiem thu bang Node (Obsidian chi dung default export la class Plugin)
module.exports.computeGroupSnap = computeGroupSnap;
module.exports.computeGroupFit = computeGroupFit;
module.exports.buildMembersByParent = buildMembersByParent;
