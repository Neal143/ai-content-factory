/**
 * factory-canvas - main.js
 * Last update: 06/10/2026 14:35 (GMT+7)
 * Vai tro: Obsidian Micro-Plugin chuyen trach dieu khien giao dien Canvas: Live RAM Data Extractor, Spatial Group Isolation, Gentle Auto-Fit, Bidirectional Edge Sync, Safe Undo Protection, Structured Debug Logging, 1-Click Re-arrange & Flyout Auto-Center.
 * Su dung khi: Chạy tự động trong Obsidian khi người dùng mở và tương tác trên file audience-hierarchy.canvas.
 * Output: 
 *   1. Smart Snap: Noi edge cha->con khi cha da co Group -> the con tu xep vao o trong ke tiep, Group chi no ra (no sang phai chi khi khong de len node ben canh, nguoc lai xuong hang moi), node phia duoi bi day xuong deu; khong co Group -> giu nguyen vi tri. Gop vao 1 buoc Undo.
 *   2. Member Fit: Vi tri the KHONG quyet dinh quan he cha-con. Tha the con o dau -> 400ms sau Group cua cha co gian om tron cac the con (theo FM), trung cong thuc renderer, gop vao 1 buoc Undo. Go quan he: xoa mui ten hoac sua FM.
 *   3. Time-Lock Cascade Suppress: Chốt chặn 1500ms dập tắt hoàn toàn vòng lặp đệ quy giữa requestSave và vault.on('modify').
 *   4. Safe Undo Protection: Bảo toàn 100% Undo Stack đơn nhất (chỉ cần 1 lần Ctrl+Z để hoàn tác quan hệ cha-con).
 *   5. Structured Debug Logging: Minh bạch hóa toàn bộ trạng thái hệ thống với các log có tiền tố [FactoryCanvas][SYNC/SNAP/FIT/UNDO/ARRANGE/ADOPT].
 *   6. 1-Click Re-arrange (Tree Layout) & Flyout Auto-Center: Khu cay (moi cay cha-con, nhanh ngang cap dat canh nhau cung tang, chuoi next step lien ke, ve tinh sat doi tac) + Khu tu do (luoi 5 cot) - xem buildArrangedCanvas; dua trong tam so do ve giua man hinh.
 *   7. Free Group Adoption: Noi edge Cha -> Group tu do (label khong co [[cha]]) -> moi the trong Group thanh con cua Cha va vao Group cua Cha (Cha chua co Group -> Group tu do thanh Group cua Cha). Gop vao 1 buoc Undo.
 *   8. Self-Write Registry: this.selfWrittenMd ghi nhan file md do plugin tu ghi FM -> factory-sync chay preview voi --skip-canvas, renderer khong ghi de canvas bang FM cu (het nhay Group sau Ctrl+Z).
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
    ZONE_GAP: 400,      // Re-arrange: khoang cach doc giua cac bang khoi va giua Khu cay - Khu tu do
    BLOCK_GAP: 440,     // Re-arrange: khoang cach ngang giua cac khoi trong cung bang
    
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
        // Group chi no sang phai khi phan no them khong de len the/group ben ngoai (vd nhanh ben canh sau Re-arrange).
        // Khong du cho -> xuong hang moi (cot 0 luon hop le); node phia duoi duoc day xuong o buoc 3.
        const outsiders = nodes.filter(n => n !== child && n !== parent && n !== group &&
            !isNodeInsideGroup(n, group) && !(n.type === 'group' && isNodeInsideGroup(group, n)));
        const canGrowTo = (sx, sy, col) => {
            const right = sx + CARD_W + PADDING_X;
            if (col === 0 || right <= group.x + group.width) return true;
            const x0 = group.x + group.width, y0 = group.y;
            const y1 = Math.max(group.y + group.height, sy + CARD_H + PADDING_X);
            return !outsiders.some(n => n.x < right && n.x + n.width > x0 && n.y < y1 && n.y + n.height > y0);
        };
        const slotX = (s) => originX + (s % COLS) * stepX;
        const slotY = (s) => originY + Math.floor(s / COLS) * stepY;
        slot = 0;
        while (!isSlotFree(slotX(slot), slotY(slot)) || !canGrowTo(slotX(slot), slotY(slot), slot % COLS)) slot++;
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

// -------------------------------------------------------------
// NHÓM 1.55: FREE GROUP ADOPTION (HAM THUAN - TEST DUOC BANG NODE)
// User noi mui ten Cha -> Group tu do (label khong co [[slug]], vd "Nhóm chưa đặt tên"):
// moi the thuoc Group tu do tro thanh con cua Cha va duoc dua vao Group cua Cha.
// Group tu do khong co chu nen thanh vien chi xac dinh duoc theo vi tri (dinh nghia Group cua Obsidian).
// -------------------------------------------------------------
/**
 * findFreeGroupMembers(nodes, group)
 * Input : nodes = canvasData.nodes; group = node Group tu do.
 * Output: [node text co slug] ma Group nho nhat chua the chinh la `group`
 *         (the nam trong Group con long ben trong - vd nhom con cua 1 thanh vien - khong tinh).
 */
const findFreeGroupMembers = (nodes, group) => {
    const groups = nodes.filter(n => n.type === 'group');
    const area = (g) => g.width * g.height;
    return nodes.filter(n => {
        if (n.type !== 'text' || !slugOfNode(n) || !isNodeInsideGroup(n, group)) return false;
        const innermost = groups.filter(g => isNodeInsideGroup(n, g)).sort((a, b) => area(a) - area(b))[0];
        return innermost.id === group.id;
    });
};

/**
 * computeFreeGroupAdoption(data, parentSlug, groupId, edgeId, directKids, keepOut)
 * Input : data = canvas.getData(); parentSlug = slug Cha; groupId = id Group tu do; edgeId = id mui ten Cha -> Group tu do;
 *         directKids = [{ childId, edgeId }] cac the dang noi mui ten truc tiep Cha -> The;
 *         keepOut = [id the] khong nhan Cha nay (vd the dang co mui ten truc tiep tu Cha khac) -> giu nguyen cho.
 * Output: { data, mode, members: [slug] } (ban sao da sua) hoac null neu Group tu do khong co the nao.
 * Logic : 'snap'   - Cha da co Group: xep tung the vao o trong cua Group Cha (computeGroupSnap), xoa Group tu do + mui ten.
 *         'adopt'  - Cha chua co Group, tong so con >= 2: Group tu do thanh Group cua Cha (label/mau chuan renderer),
 *                    the con dang noi truc tiep duoc xep vao, Group om khit cac con; Cha la Big -> can giua tren Group.
 *         'single' - Cha chua co Group, chi 1 con: doi mui ten Cha -> Group thanh Cha -> The, xoa Group tu do.
 */
const computeFreeGroupAdoption = (data, parentSlug, groupId, edgeId, directKids = [], keepOut = []) => {
    const C = CANVAS_CONFIG;
    let out = JSON.parse(JSON.stringify(data));
    out.nodes = out.nodes || [];
    out.edges = out.edges || [];
    const group = out.nodes.find(n => n.id === groupId && n.type === 'group' && !slugOfNode(n));
    const parent = out.nodes.find(n => n.type === 'text' && slugOfNode(n) === parentSlug);
    if (!group || !parent) return null;

    // 1. The thuoc Group tu do (tru the Cha va keepOut), thu tu doc tren -> duoi, trai -> phai (giu bo cuc user da xep)
    const members = findFreeGroupMembers(out.nodes, group)
        .filter(n => n.id !== parent.id && !keepOut.includes(n.id))
        .sort((a, b) => (a.y - b.y) || (a.x - b.x));
    if (!members.length) return null;
    const memberIds = members.map(n => n.id);
    const memberSlugs = members.map(slugOfNode);
    const dropFreeGroup = (d) => {
        d.nodes = d.nodes.filter(n => n.id !== groupId);
        d.edges = d.edges.filter(e => e.fromNode !== groupId && e.toNode !== groupId);
        return d;
    };

    // 2. 'snap': Cha da co Group -> moi thanh vien vao o trong ke tiep (mui ten Cha -> Group tu do bi go o lan snap dau)
    if (out.nodes.some(n => n.type === 'group' && slugOfNode(n) === parentSlug)) {
        for (const id of memberIds) {
            const res = computeGroupSnap(out, id, parentSlug, edgeId);
            if (res) out = res.data;
        }
        return { data: dropFreeGroup(out), mode: 'snap', members: memberSlugs };
    }

    // 3. 'single': Cha chua co Group va tong cong chi 1 con -> noi thang Cha -> The (renderer khong tao Group cho 1 con)
    const kids = directKids.filter(k => !memberIds.includes(k.childId));
    const edge = out.edges.find(e => e.id === edgeId);
    if (members.length + kids.length < 2) {
        if (edge) Object.assign(edge, { toNode: memberIds[0], toSide: 'top', color: C.COLOR_EDGE_PHA_HE });
        return { data: dropFreeGroup(out), mode: 'single', members: memberSlugs };
    }

    // 4. 'adopt': Group tu do thanh Group cua Cha; con dang noi truc tiep duoc xep vao Group (go mui ten truc tiep)
    const isBig = String(parent.text || '').includes('#big');
    Object.assign(group, { label: `📦 NHÓM CON (Little Audiences): [[${parentSlug}]]`, color: isBig ? C.COLOR_GROUP_L1 : C.COLOR_GROUP_L2 });
    if (edge) Object.assign(edge, { toSide: 'top', color: C.COLOR_EDGE_PHA_HE });
    for (const k of kids) {
        const res = computeGroupSnap(out, k.childId, parentSlug, k.edgeId);
        if (res) out = res.data;
    }

    // 5. Group om khit cac con (cong thuc renderer); Cha la Big -> dat chinh giua phia tren Group (renderer luon dat lai Big)
    const ids = new Set([...memberIds, ...kids.map(k => k.childId)]);
    const fit = computeGroupFit(out, { [parentSlug]: out.nodes.filter(n => ids.has(n.id)).map(slugOfNode) });
    if (fit) out = fit.data;
    if (isBig) {
        const g = out.nodes.find(n => n.id === groupId);
        const b = out.nodes.find(n => n.id === parent.id);
        Object.assign(b, { width: C.BIG_CARD_W, height: C.BIG_CARD_H, x: g.x + g.width / 2 - C.BIG_CARD_W / 2, y: g.y - C.BIG_CARD_H - C.MOTHER_OFFSET_Y });
    }
    return { data: out, mode: 'adopt', members: memberSlugs };
};

// -------------------------------------------------------------
// NHÓM 1.6: RE-ARRANGE LAYOUT (HAM THUAN, KHONG PHU THUOC OBSIDIAN - TEST DUOC BANG NODE)
// Thiet ke: factory-canvas-rearrange-design.md. Cha-con quyet dinh the nam o dau; next step quyet dinh
// the nam canh ai (khi khong pha cha-con); the khong lien ket gom ve Khu tu do.
// -------------------------------------------------------------
/**
 * computeArrangeLayout(cards, parentMap, nextStepMap)
 * Input : cards = [{ id, slug, x, y, isBig }] (moi slug 1 the); parentMap/nextStepMap = { slug: Iterable<slug> } tu Frontmatter.
 * Output: { pos: { id: {x, y, width, height} }, groups: [{ parentSlug, x, y, width, height }], primaryKids: { slugCha: [slugCon] }, bigSlug }
 */
const computeArrangeLayout = (cards, parentMap, nextStepMap) => {
    const C = CANVAS_CONFIG;
    const stepX = C.CARD_W + C.GAP_X, stepY = C.CARD_H + C.GAP_Y;
    const bySlug = new Map(cards.map(c => [c.slug, c]));
    const sizeOf = (s) => (bySlug.get(s).isBig ? [C.BIG_CARD_W, C.BIG_CARD_H] : [C.CARD_W, C.CARD_H]);

    // 1. Khoa thu tu doc on dinh: hang luoi (theo tam the) -> x -> slug. Chay Re-arrange lan 2 cho cung ket qua.
    const readKey = (s) => { const c = bySlug.get(s); return [Math.floor((c.y + sizeOf(s)[1] / 2) / stepY), c.x, s]; };
    const cmp = (a, b) => {
        const ka = readKey(a), kb = readKey(b);
        for (let i = 0; i < 3; i++) { if (ka[i] < kb[i]) return -1; if (ka[i] > kb[i]) return 1; }
        return 0;
    };

    // 2. Quan he chi tinh giua cac the dang co tren canvas
    const parentsOf = {}, kidsAll = {}, nextOut = {}, nextIn = {};
    for (const s of bySlug.keys()) { parentsOf[s] = []; kidsAll[s] = []; nextOut[s] = []; nextIn[s] = []; }
    for (const s of bySlug.keys()) {
        for (const p of (parentMap[s] || [])) if (bySlug.has(p) && p !== s && !parentsOf[s].includes(p)) { parentsOf[s].push(p); kidsAll[p].push(s); }
        for (const t of (nextStepMap[s] || [])) if (bySlug.has(t) && t !== s && !nextOut[s].includes(t)) { nextOut[s].push(t); nextIn[t].push(s); }
    }
    for (const s of bySlug.keys()) { kidsAll[s].sort(cmp); nextOut[s].sort(cmp); nextIn[s].sort(cmp); }
    const all = [...bySlug.keys()].sort(cmp);

    // 3. Gan cha chinh: duyet tu goc (cha truoc con). The nhieu cha chi xep 1 lan, duoi cha duoc duyet toi dau tien.
    const primaryKids = {}, inTree = new Set(), treeRoots = [];
    const claim = (root) => {
        inTree.add(root); treeRoots.push(root);
        const queue = [root];
        while (queue.length) {
            const p = queue.shift();
            for (const k of kidsAll[p]) {
                if (inTree.has(k)) continue;
                inTree.add(k); (primaryKids[p] = primaryKids[p] || []).push(k); queue.push(k);
            }
        }
    };
    const big = cards.find(c => c.isBig && parentsOf[c.slug].length === 0);
    const bigSlug = big ? big.slug : null;
    if (bigSlug) claim(bigSlug);
    for (const s of all) if (!inTree.has(s) && parentsOf[s].length === 0 && kidsAll[s].length > 0) claim(s);
    for (const s of all) if (!inTree.has(s) && parentsOf[s].length > 0) claim(s); // vong cha-con khong co goc: cat vong tai the dau tien
    const kidsOf = (s) => primaryKids[s] || [];

    // 4. Gom the thanh chuoi next step (chi xet lien ket trong tap members). Chuoi xep theo khoa doc cua the dau.
    const toChains = (members) => {
        const set = new Set(members), seen = new Set(), chains = [];
        for (const s0 of [...members].sort(cmp)) {
            if (seen.has(s0)) continue;
            const compSet = new Set([s0]), stack = [s0];
            while (stack.length) {
                const u = stack.pop();
                for (const v of [...nextOut[u], ...nextIn[u]]) if (set.has(v) && !compSet.has(v)) { compSet.add(v); stack.push(v); }
            }
            const comp = [...compSet].sort(cmp), chain = [];
            const visit = (u) => { if (seen.has(u)) return; seen.add(u); chain.push(u); for (const v of nextOut[u]) if (compSet.has(v)) visit(v); };
            for (const st of comp.filter(u => !nextIn[u].some(v => compSet.has(v)))) visit(st);
            for (const u of comp) visit(u); // con sot do vong next step: cat vong tai the co khoa doc nho nhat
            chains.push(chain);
        }
        return chains.sort((a, b) => cmp(a[0], b[0]));
    };

    // 5. The ngoai cay: ve tinh (next step toi the cay), chuoi doc lap, the tu do
    const outside = all.filter(s => !inTree.has(s));
    const freeCards = outside.filter(s => nextOut[s].length + nextIn[s].length === 0);
    const satByAnchor = {}, soloChains = [];
    for (const chain of toChains(outside.filter(s => nextOut[s].length + nextIn[s].length > 0))) {
        let anchor = null;
        for (const s of chain) {
            const o = nextOut[s].find(t => inTree.has(t)); if (o) { anchor = { tree: o, side: 'left' }; break; }
            const i = nextIn[s].find(t => inTree.has(t)); if (i) { anchor = { tree: i, side: 'right' }; break; }
        }
        if (!anchor) { soloChains.push(chain); continue; }
        const slot = (satByAnchor[anchor.tree] = satByAnchor[anchor.tree] || { left: [], right: [] });
        slot[anchor.side].push(chain);
    }

    // 6. Box cuc bo: items (the), groups (khung), bien minX/maxX/maxY, anchorX (diem mui ten di vao tu phia tren)
    const newBox = () => ({ items: [], groups: [], minX: Infinity, maxX: -Infinity, maxY: -Infinity, anchorX: 0 });
    const addItem = (b, s, x, y) => {
        const [w, h] = sizeOf(s);
        b.items.push({ s, x, y, w, h });
        b.minX = Math.min(b.minX, x); b.maxX = Math.max(b.maxX, x + w); b.maxY = Math.max(b.maxY, y + h);
    };
    const addGroup = (b, g) => {
        b.groups.push(g);
        b.minX = Math.min(b.minX, g.x); b.maxX = Math.max(b.maxX, g.x + g.width); b.maxY = Math.max(b.maxY, g.y + g.height);
    };
    const merge = (b, o, dx, dy) => {
        for (const it of o.items) addItem(b, it.s, it.x + dx, it.y + dy);
        for (const g of o.groups) addGroup(b, { ...g, x: g.x + dx, y: g.y + dy });
    };
    // Chuoi ve tinh dat sat ben trai (xEdge = mep trai doi tac) hoac ben phai (xEdge = mep phai), cung hang y
    const placeSats = (b, chains, side, xEdge, y) => {
        let cursor = xEdge;
        for (const chain of chains) {
            const w = chain.length * stepX - C.GAP_X;
            const x0 = side === 'left' ? cursor - C.GAP_X - w : cursor + C.GAP_X;
            chain.forEach((s, i) => addItem(b, s, x0 + i * stepX, y));
            cursor = side === 'left' ? x0 : x0 + w;
        }
    };

    // 7. Khoi con cua p (y = 0 la dinh Group ao): 1 con -> the con dung rieng; >= 2 con -> Group luoi + tang nhanh con
    const layoutKids = (p) => {
        const kids = kidsOf(p);
        if (kids.length === 0) return null;
        if (kids.length === 1) {
            const sb = layoutStanding(kids[0]);
            const b = newBox(); merge(b, sb, 0, C.PADDING_Y); b.anchorX = sb.anchorX;
            return b;
        }
        // 7.1 Luoi: chuoi la truoc, chuoi co the co con xuong cuoi; chuoi <= COLS khong bi cat ngang hang
        const isBranch = (ch) => ch.some(s => kidsOf(s).length > 0);
        const chains = toChains(kids);
        const cell = {};
        let idx = 0;
        for (const ch of [...chains.filter(ch => !isBranch(ch)), ...chains.filter(isBranch)]) {
            const col = idx % C.COLS;
            if (col !== 0 && col + ch.length > C.COLS) idx += C.COLS - col; // chuoi khong vua phan con lai -> sang hang moi
            for (const s of ch) { cell[s] = [idx % C.COLS, Math.floor(idx / C.COLS)]; idx++; }
        }
        const b = newBox();
        for (const s of kids) addItem(b, s, C.PADDING_X + cell[s][0] * stepX, C.PADDING_Y + cell[s][1] * stepY);
        const gW = Math.max(...b.items.map(it => it.x + it.w)) + C.PADDING_X;
        const gH = Math.max(...b.items.map(it => it.y + it.h)) + C.PADDING_X;
        addGroup(b, { parentSlug: p, x: 0, y: 0, width: gW, height: gH });
        // 7.2 Ve tinh cua the trong Group: sat ngoai mep Group, cung hang voi doi tac
        const rows = {};
        for (const s of kids) if (satByAnchor[s]) (rows[cell[s][1]] = rows[cell[s][1]] || []).push(s);
        for (const [r, list] of Object.entries(rows)) {
            const y = C.PADDING_Y + Number(r) * stepY;
            list.sort((a, c) => cell[a][0] - cell[c][0]);
            placeSats(b, list.flatMap(s => satByAnchor[s].left), 'left', 0, y);
            placeSats(b, [...list].reverse().flatMap(s => satByAnchor[s].right), 'right', gW, y);
        }
        // 7.3 Tang nhanh con: cac nhanh dat canh nhau duoi Group theo thu tu luoi, can giua duoi the cha neu con cho
        let prevMaxX = null;
        const branchKids = kids.filter(s => kidsOf(s).length > 0).sort((a, c) => (cell[a][1] - cell[c][1]) || (cell[a][0] - cell[c][0]));
        for (const s of branchKids) {
            const kb = layoutKids(s);
            const it = b.items.find(i => i.s === s);
            let dx = it.x + it.w / 2 - kb.anchorX;
            if (prevMaxX !== null) dx = Math.max(dx, prevMaxX + C.GAP_X - kb.minX);
            merge(b, kb, dx, gH + C.TIER_GAP);
            prevMaxX = kb.maxX + dx;
        }
        b.anchorX = gW / 2;
        return b;
    };
    // 8. The dung rieng: can giua tren khoi con (mui ten doc), dinh khoi con cach day the MOTHER_OFFSET_Y; ve tinh 2 ben
    const layoutStanding = (s) => {
        const b = newBox(), [w, h] = sizeOf(s);
        const kb = layoutKids(s);
        const x = kb ? kb.anchorX - w / 2 : 0;
        addItem(b, s, x, 0);
        if (kb) merge(b, kb, 0, h + C.MOTHER_OFFSET_Y);
        const sats = satByAnchor[s];
        if (sats) { placeSats(b, sats.left, 'left', x, 0); placeSats(b, sats.right, 'right', x + w, 0); }
        b.anchorX = x + w / 2;
        return b;
    };

    // 9. Dat khoi: bang 1 = cay Big (Group L1 tai START_X - PADDING_X nhu bo cuc cu); bang 2+ = cay khac + chuoi doc lap
    const pos = {}, groups = [];
    const put = (b, dx, dy) => {
        for (const it of b.items) pos[bySlug.get(it.s).id] = { x: it.x + dx, y: it.y + dy, width: it.w, height: it.h };
        for (const g of b.groups) groups.push({ ...g, x: g.x + dx, y: g.y + dy });
    };
    const left0 = C.START_X - C.PADDING_X;
    let bandY = C.START_Y - C.PADDING_Y - C.BIG_CARD_H - C.MOTHER_OFFSET_Y;
    let zoneBottom = null, maxBandW = C.COLS * stepX - C.GAP_X + 2 * C.PADDING_X;
    if (bigSlug) {
        const bb = layoutStanding(bigSlug);
        const g1 = bb.groups.find(g => g.parentSlug === bigSlug);
        const hasKids = kidsOf(bigSlug).length > 0;
        // Big khong co con: renderer dat Big theo bbox rong mac dinh (50, 550, 2000, 1000) -> dat trung de renderer khong ghi de
        const dx = hasKids ? left0 - (g1 ? g1.x : bb.minX) : 50 + 1000 - C.BIG_CARD_W / 2 - bb.items.find(it => it.s === bigSlug).x;
        const dy = hasKids ? bandY : 550 - C.BIG_CARD_H - C.MOTHER_OFFSET_Y;
        put(bb, dx, dy);
        zoneBottom = dy + bb.maxY;
        maxBandW = Math.max(maxBandW, bb.maxX - bb.minX);
        bandY = zoneBottom + C.ZONE_GAP;
    }
    const soloBox = (ch) => { const b = newBox(); ch.forEach((s, i) => addItem(b, s, i * stepX, 0)); return b; };
    const units = [
        ...toChains(treeRoots.filter(s => s !== bigSlug)).map(ch => ({ head: ch[0], boxes: ch.map(layoutStanding) })),
        ...soloChains.map(ch => ({ head: ch[0], boxes: [soloBox(ch)] }))
    ].sort((a, b) => cmp(a.head, b.head));
    let cursor = left0, bandBottom = null;
    for (const u of units) for (const b of u.boxes) {
        const w = b.maxX - b.minX;
        if (cursor > left0 && cursor + w > left0 + maxBandW) { bandY = bandBottom + C.ZONE_GAP; cursor = left0; }
        put(b, cursor - b.minX, bandY);
        cursor += w + C.BLOCK_GAP;
        bandBottom = Math.max(bandBottom === null ? -Infinity : bandBottom, bandY + b.maxY);
        zoneBottom = Math.max(zoneBottom === null ? -Infinity : zoneBottom, bandBottom);
    }

    // 10. Khu tu do: luoi COLS cot lien mach theo thu tu doc, cach Khu cay ZONE_GAP
    const freeY = zoneBottom === null ? C.START_Y : zoneBottom + C.ZONE_GAP;
    freeCards.forEach((s, i) => {
        pos[bySlug.get(s).id] = { x: C.START_X + (i % C.COLS) * stepX, y: freeY + Math.floor(i / C.COLS) * stepY, width: C.CARD_W, height: C.CARD_H };
    });
    return { pos, groups, primaryKids, bigSlug };
};

/**
 * buildArrangedCanvas(canvasData, parentMap, nextStepMap)
 * Input : canvasData doc tu file .canvas; parentMap/nextStepMap tu Frontmatter.
 * Output: { data, directEdges } - data = ban sao canvas da Re-arrange (node, group, edge); directEdges = { slugCon: slugCha } cho mui ten Cha->The.
 * Logic : dat vi tri theo computeArrangeLayout; cap nhat/tao/xoa Group theo cha co >= 2 con; sinh lai mui ten pha he + job step, giu mau user.
 */
const buildArrangedCanvas = (canvasData, parentMap, nextStepMap) => {
    const data = JSON.parse(JSON.stringify(canvasData));
    const nodes = data.nodes || [];
    // 1. Chi muc the audience theo slug (bo truong 'slug' do phien ban cu ghi nham vao file -> renderer ghi de canvas)
    const textBySlug = new Map();
    for (const n of nodes) {
        delete n.slug;
        if (n.type !== 'text') continue;
        const s = slugOfNode(n);
        if (s && !textBySlug.has(s)) textBySlug.set(s, n);
    }
    const cards = [...textBySlug].map(([slug, n]) => ({ id: n.id, slug, x: n.x, y: n.y, isBig: String(n.text || '').includes('#big') }));
    const layout = computeArrangeLayout(cards, parentMap, nextStepMap);
    const nodeById = new Map(nodes.map(n => [n.id, n]));
    for (const [id, p] of Object.entries(layout.pos)) Object.assign(nodeById.get(id), p);

    // 2. Group: cap nhat theo layout; xoa group cha khong con >= 2 con, group trung lap, group khong co [[cha]] (Group tu do, group rac cu)
    const wanted = new Map(layout.groups.map(g => [g.parentSlug, g]));
    const groupIdBySlug = {};
    data.nodes = nodes.filter(n => {
        if (n.type !== 'group') return true;
        const ps = slugOfNode(n);
        if (!ps) return false; // Group khong co [[cha]] (Group tu do, group rac cu): renderer khong sinh -> xoa
        const g = wanted.get(ps);
        if (!g || groupIdBySlug[ps]) return false;
        Object.assign(n, { x: g.x, y: g.y, width: g.width, height: g.height });
        groupIdBySlug[ps] = n.id;
        return true;
    });
    for (const g of layout.groups) {
        if (groupIdBySlug[g.parentSlug]) continue;
        const isL1 = g.parentSlug === layout.bigSlug;
        const id = isL1 ? 'group_little_audiences' : `group_sub_${g.parentSlug}`;
        data.nodes.unshift({
            id, type: 'group', label: `📦 NHÓM CON (Little Audiences): [[${g.parentSlug}]]`,
            x: g.x, y: g.y, width: g.width, height: g.height,
            color: isL1 ? CANVAS_CONFIG.COLOR_GROUP_L1 : CANVAS_CONFIG.COLOR_GROUP_L2
        });
        groupIdBySlug[g.parentSlug] = id;
    }

    // 3. Mui ten: pha he theo cha chinh (>= 2 con -> Cha->Group, 1 con -> Cha->The) + job step.
    //    Giu id + mau cua edge cu cung (from, side, to, side) - giong renderer - de ket qua on dinh giua cac lan chay.
    const idOf = (s) => (textBySlug.get(s) || {}).id;
    const oldByKey = new Map((data.edges || []).map(e => [`${e.fromNode}|${e.fromSide}|${e.toNode}|${e.toSide}`, e]));
    const edges = [], directEdges = {}, usedIds = new Set();
    let counter = 1;
    const pushEdge = (baseId, fromNode, fromSide, toNode, toSide, defColor) => {
        const old = oldByKey.get(`${fromNode}|${fromSide}|${toNode}|${toSide}`);
        let id = old ? old.id : baseId;
        while (usedIds.has(id)) id = `${baseId}_${counter++}`;
        usedIds.add(id);
        edges.push({ id, fromNode, fromSide, toNode, toSide, color: (old && old.color) || defColor });
    };
    for (const [p, kids] of Object.entries(layout.primaryKids)) {
        const fromId = idOf(p);
        const toId = kids.length > 1 ? groupIdBySlug[p] : idOf(kids[0]);
        if (!fromId || !toId) continue;
        const baseId = p === layout.bigSlug
            ? (kids.length > 1 ? 'edge_root_to_group' : 'edge_root_to_single_child')
            : `edge_pha_he_sub_${kids.length > 1 ? '' : 'single_'}${counter++}`;
        pushEdge(baseId, fromId, 'bottom', toId, 'top', CANVAS_CONFIG.COLOR_EDGE_PHA_HE);
        if (kids.length === 1) directEdges[kids[0]] = p;
    }
    for (const [from, tos] of Object.entries(nextStepMap || {})) {
        const fromId = idOf(from);
        if (!fromId) continue;
        for (const to of tos) {
            const toId = idOf(to);
            if (!toId || toId === fromId) continue;
            pushEdge(`edge_job_step_${counter++}`, fromId, 'right', toId, 'left', CANVAS_CONFIG.COLOR_EDGE_JOB_STEP);
        }
    }
    data.edges = edges;
    return { data, directEdges };
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

        // --- SELF-WRITE REGISTRY (doc boi plugin factory-sync) ---
        // path md -> thoi diem plugin ghi FM. factory-sync thay modify cua file nay (< 3s) -> preview --skip-canvas:
        // canvas da la nguon su that; renderer doc FM truoc/canvas sau ~3s se ghi de sai (Group no ra roi co lai sau Undo).
        this.selfWrittenMd = new Map();
        const markSelfWrite = (path) => {
            const now = Date.now();
            for (const [p, t] of this.selfWrittenMd) if (now - t > 10000) this.selfWrittenMd.delete(p); // don muc cu
            this.selfWrittenMd.set(path, now);
        };

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
            const freeGroupLinks = []; // { parentSlug, groupId, edgeId }: mui ten Cha -> Group tu do (label khong co [[cha]])
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
                    // B. Mui ten tro vao Khung Group CUA CHA ([[cha]] trong label) -> Ghi nhan Cha dang ket noi pha he voi nhom
                    // (TUYET DOI khong dung toa do Bounding Box de phong doan/gan thanh vien)
                    else if (toNode.type === 'group' && extractSlug(toNode.label)) {
                        activeGroupParents.add(fromSlug);
                    }
                    // C. Mui ten tro vao Group TU DO (label khong co [[cha]]): moi the thuoc Group thanh con cua Cha.
                    //    Group tu do khong co chu nen thanh vien xac dinh theo vi tri (findFreeGroupMembers).
                    //    Mui ten truc tiep vao the uu tien hon (ghi de o nhanh A neu xu ly sau).
                    else if (toNode.type === 'group') {
                        freeGroupLinks.push({ parentSlug: fromSlug, groupId: toNode.id, edgeId: edge.id });
                        for (const m of findFreeGroupMembers(nodes, toNode)) {
                            if (m.slug && m.slug !== fromSlug && !activeDirectEdges[m.slug]) {
                                activeDirectEdges[m.slug] = fromSlug;
                                logFC('SYNC', `Thẻ [${m.slug}] thuộc Group tự do -> nhận cha [${fromSlug}]`);
                            }
                        }
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
                    // 2.5a FREE GROUP ADOPTION: Cha -> Group tu do. Moi Group tu do chi nhan Cha cua mui ten dau tien.
                    let adoptedCount = 0;
                    const handledKids = new Set(); // con noi truc tiep da duoc xep vao Group o mode 'adopt' -> bo qua o Smart Snap
                    const seenFreeGroups = new Set();
                    for (const link of freeGroupLinks) {
                        if (seenFreeGroups.has(link.groupId)) continue;
                        seenFreeGroups.add(link.groupId);
                        const kidEntries = Object.entries(directEdgeInfo)
                            .filter(([c, info]) => info.parentSlug === link.parentSlug && activeDirectEdges[c] === link.parentSlug);
                        const keepOut = nodes.filter(n => n.slug && activeDirectEdges[n.slug] !== link.parentSlug).map(n => n.id);
                        const res = computeFreeGroupAdoption(snapCanvas.getData(), link.parentSlug, link.groupId, link.edgeId,
                            kidEntries.map(([, info]) => ({ childId: info.childId, edgeId: info.edgeId })), keepOut);
                        if (!res) continue;
                        snapCanvas.importData(res.data, true);
                        adoptedCount++;
                        if (res.mode === 'adopt') kidEntries.forEach(([c]) => handledKids.add(c));
                        logFC('ADOPT', `Group tự do [${link.groupId}] -> [${link.parentSlug}] (${res.mode}): ${res.members.join(', ')}`);
                    }

                    let snappedCount = 0;
                    for (const [childSlug, info] of Object.entries(directEdgeInfo)) {
                        if (handledKids.has(childSlug)) continue;
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
                    if (snappedCount > 0 || adoptedCount > 0 || fitted) {
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
                        markSelfWrite(file.path); // factory-sync: lan ghi nay khong render canvas
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

            // 1. Tinh bo cuc (Khu cay + Khu tu do), Group va mui ten bang ham thuan buildArrangedCanvas (NHOM 1.6)
            const { parentMap: vParentMap, nextStepMap: vNextStepMap } = await getVaultAudienceData();
            const { data: canvasData, directEdges } = buildArrangedCanvas(JSON.parse(raw), vParentMap, vNextStepMap);

            // 2. Dong bo bo nho dem mui ten Cha->The (phuc vu bat Undo/Delete o lan sync tiep theo)
            previousDirectEdges = directEdges;
            logFC('ARRANGE', `Re-arrange: ${canvasData.nodes.length} node, ${canvasData.edges.length} edge.`);

            // 3. Ghi đĩa Canvas Data
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
module.exports.computeArrangeLayout = computeArrangeLayout;
module.exports.buildArrangedCanvas = buildArrangedCanvas;
module.exports.findFreeGroupMembers = findFreeGroupMembers;
module.exports.computeFreeGroupAdoption = computeFreeGroupAdoption;
