/**
 * Ten file: ImportEngineView.ts
 * Last update: 03/11/2026 15:52 (GMT+7)
 * Vai tro: Bang dieu khien Theo doi Fanpage, Trang ca nhan & Bai viet (hien thi truc dien) kem Ngan keo Thu thap/Nhap du lieu Engagement va Cai dat Quet nang cao (mac dinh an de tiet kiem dien tich).
 * Duoc su dung khi nao?: Khi user mo tab Analytics tren Dashboard.
 * Output:
 *  1. Thanh Header gon nhe hien thi so Trang, so Bai dang theo doi va Chu ky cap nhat du lieu moi + Nut bat/tat ngan keo "➕ Thêm nguồn / Cài đặt quét".
 *  2. Tab "Quét tự động Facebook (Fanpage / Cá nhân / Post URL)" tich hop:
 *     - Cong tac chay ngam, binh luan cap 2 & Ket noi Nick FB phu.
 *     - 2 khung nhap Fanpage/Trang ca nhan & Post URL le (ho tro Phan loai: Doi thu, Thuong hieu, Khac va Tu tao nhan moi).
 *     - Bang Du bao Khoi luong Theo doi & Chu ky Cap nhat Chi so Tuong tac (tinh toan tuc thoi khi user nhap them trang/bai viet).
 *     - Khoi Cai dat Quet nang cao & Nguong tu dong ngung quet cho bai cu (3 che do + Batch Size + 6 chi so khoa cung).
 *  3. Bang 1 (Luon hien thi): Danh sach cac Fanpage / Trang ca nhan user da chi dinh theo doi (doi phan loai hoac tao nhan moi se tu dong dong bo sang toan bo bang bai viet va bieu do).
 *  4. Bang 2 (Luon hien thi): Danh sach Bai viet da thu thap (tich hop Bo loc Thoi gian khong co Gop/Moc, Sparkline 5 ngay, Xem truoc & Luu vao Vault, xoa don/hang loat, va ho tro nhay/highlight bai viet tu bieu do Engagement).
 * Tom tat logic hoat dong: Khoa cung cac tham so ky thuat bao ve IP o tang he thong; ho tro Dual-Context (Tang 3 Khong Cookie + Tang 2 Co Cookie nick phu); dong bo nhan phan loai (Doi thu, Thuong hieu, Khac, Nhan tu tao) xuyen suot 4 bang va bieu do.
 */

import { App, Modal, TFile, setIcon } from "obsidian";
import {
	EngagementStore,
	EngagementRecord,
	PostSparkline5D,
	TimelinePeriodPostItem,
	formatSourceTypeLabel,
} from "../data/EngagementStore";
import {
	DateRangeSelection,
	renderDateRangePickerButton,
} from "./DateRangePickerPopover";

// Hàm tiện ích gắn Vector Icon đơn sắc chuẩn SF Symbols / Lucide vào nút bấm hoặc phần tử DOM
function setBtnContent(el: HTMLElement, iconName: string, labelText?: string, spinning = false): void {
	el.empty();
	const ic = el.createSpan({ cls: `cc-icon ${spinning ? "is-spinning" : ""}` });
	setIcon(ic, iconName);
	if (labelText) {
		el.createSpan({ text: labelText });
	}
}

function createMetricChip(parent: HTMLElement, iconName: string, textValue: string, extraCls = "content-compass-fb-metric-chip"): HTMLElement {
	const chip = parent.createSpan({ cls: extraCls });
	const ic = chip.createSpan({ cls: "cc-icon" });
	setIcon(ic, iconName);
	chip.createSpan({ text: textValue });
	return chip;
}

// Hàm vẽ biểu đồ Line nhỏ (5-Day Score Sparkline) nằm gọn trên Dòng 1 cạnh chỉ số Score
// Nếu bài mới quét lần đầu (chỉ có 1 ngày có dữ liệu): chỉ vẽ 1 chấm tròn tại ngày đó, các ngày trước ghi rõ "Không có dữ liệu"
function renderPostSparkline5D(parent: HTMLElement, spark: PostSparkline5D, isTop5: boolean): void {
	const wrap = parent.createDiv({
		cls: `cc-post-sparkline-wrap ${spark.isFirstScan ? "is-single-point" : ""}`,
	});
	const vals = spark.dailyScores;
	const numericVals = vals.filter((v): v is number => v !== null);
	const minV = numericVals.length > 0 ? Math.min(...numericVals) : 0;
	const maxV = numericVals.length > 0 ? Math.max(...numericVals) : 0;
	const range = maxV - minV;

	const w = 52;
	const h = 18;
	const padX = 4;
	const padY = 3.5;
	const innerW = w - padX * 2;
	const innerH = h - padY * 2;
	const midY = Number((h / 2).toFixed(1));

	const validCoords: Array<{ idx: number; x: number; y: number; val: number }> = [];
	const emptyXs: number[] = [];

	vals.forEach((v, idx) => {
		const x = Number((padX + (idx / Math.max(1, vals.length - 1)) * innerW).toFixed(1));
		if (v === null) {
			emptyXs.push(x);
		} else {
			const y =
				numericVals.length <= 1 || range === 0
					? midY
					: Number((padY + innerH - ((v - minV) / range) * innerH).toFixed(1));
			validCoords.push({ idx, x, y, val: v });
		}
	});

	const strokeColor = "#0a84ff";
	const fillColor = "rgba(10, 132, 255, 0.14)";

	const svgNs = "http://www.w3.org/2000/svg";
	const svg = document.createElementNS(svgNs, "svg");
	svg.setAttribute("class", "cc-post-sparkline-svg");
	svg.setAttribute("width", String(w));
	svg.setAttribute("height", String(h));
	svg.setAttribute("viewBox", `0 0 ${w} ${h}`);

	// Trục ngang nét đứt mờ làm khung tham chiếu 5 ngày
	const baseLine = document.createElementNS(svgNs, "line");
	baseLine.setAttribute("x1", String(padX));
	baseLine.setAttribute("y1", String(midY));
	baseLine.setAttribute("x2", String(w - padX));
	baseLine.setAttribute("y2", String(midY));
	baseLine.setAttribute("stroke", "hsla(0, 0%, 55%, 0.25)");
	baseLine.setAttribute("stroke-width", "1");
	baseLine.setAttribute("stroke-dasharray", "2,2");
	svg.appendChild(baseLine);

	// Các ngày không có dữ liệu chỉ hiển thị chấm xám cực nhỏ trên trục nét đứt
	for (const ex of emptyXs) {
		const emptyTick = document.createElementNS(svgNs, "circle");
		emptyTick.setAttribute("cx", String(ex));
		emptyTick.setAttribute("cy", String(midY));
		emptyTick.setAttribute("r", "1.1");
		emptyTick.setAttribute("fill", "hsla(0, 0%, 55%, 0.35)");
		svg.appendChild(emptyTick);
	}

	if (validCoords.length === 1) {
		// Bài mới quét lần đầu: CHỈ hiển thị 1 chấm dữ liệu duy nhất (kèm vòng halo nhẹ), tuyệt đối không vẽ đường nối giả
		const singlePt = validCoords[0];
		const halo = document.createElementNS(svgNs, "circle");
		halo.setAttribute("cx", String(singlePt.x));
		halo.setAttribute("cy", String(singlePt.y));
		halo.setAttribute("r", "4.8");
		halo.setAttribute("fill", fillColor);
		svg.appendChild(halo);

		const dot = document.createElementNS(svgNs, "circle");
		dot.setAttribute("cx", String(singlePt.x));
		dot.setAttribute("cy", String(singlePt.y));
		dot.setAttribute("r", "2.4");
		dot.setAttribute("fill", strokeColor);
		svg.appendChild(dot);
	} else if (validCoords.length >= 2) {
		// Bài đã có dữ liệu từ 2 ngày trở lên: Vẽ đường nối giữa các ngày thực sự có dữ liệu
		const linePoints = validCoords.map((p) => `${p.x},${p.y}`).join(" ");
		const firstPt = validCoords[0];
		const lastPt = validCoords[validCoords.length - 1];
		const areaPoints = `${firstPt.x},${h - 1} ${linePoints} ${lastPt.x},${h - 1}`;

		const polygon = document.createElementNS(svgNs, "polygon");
		polygon.setAttribute("points", areaPoints);
		polygon.setAttribute("fill", fillColor);
		svg.appendChild(polygon);

		const polyline = document.createElementNS(svgNs, "polyline");
		polyline.setAttribute("points", linePoints);
		polyline.setAttribute("fill", "none");
		polyline.setAttribute("stroke", strokeColor);
		polyline.setAttribute("stroke-width", "1.6");
		polyline.setAttribute("stroke-linecap", "round");
		polyline.setAttribute("stroke-linejoin", "round");
		svg.appendChild(polyline);

		const dot = document.createElementNS(svgNs, "circle");
		dot.setAttribute("cx", String(lastPt.x));
		dot.setAttribute("cy", String(lastPt.y));
		dot.setAttribute("r", "2.2");
		dot.setAttribute("fill", strokeColor);
		svg.appendChild(dot);
	}

	wrap.appendChild(svg);

	if (spark.delta5d !== null && spark.delta5d > 0) {
		wrap.createSpan({
			cls: "cc-post-sparkline-delta is-up",
			text: `+${spark.delta5d}`,
		});
	}

	const detailLines = spark.dayLabels.map((lbl, idx) => {
		const dayVal = vals[idx];
		const suffix = idx === 4 ? " (Hôm nay)" : "";
		if (dayVal === null) {
			return `• ${lbl}${suffix}: Không có dữ liệu`;
		}
		return `• ${lbl}${suffix}: ${dayVal} điểm`;
	});

	let footerNote = "";
	if (spark.isFirstScan || validCoords.length <= 1) {
		footerNote =
			"Trạng thái: Mới quét lần đầu (chỉ có 1 mốc dữ liệu, các ngày trước chưa có dữ liệu để tính tăng trưởng)";
	} else {
		const firstDayLbl = spark.dayLabels[validCoords[0].idx];
		const lastDayLbl = spark.dayLabels[validCoords[validCoords.length - 1].idx];
		const dVal = spark.delta5d || 0;
		const deltaSign = dVal > 0 ? `+${dVal}` : String(dVal);
		footerNote = `Tăng trưởng (${firstDayLbl} → ${lastDayLbl}): ${deltaSign} điểm`;
	}

	wrap.setAttribute(
		"title",
		`Dữ liệu Score 5 ngày gần nhất:\n${detailLines.join("\n")}\n────────────────────\n${footerNote}`
	);
}

// Nhom 1: Dinh nghia cau truc du lieu Watchlist, State va Bo dem bai viet (Khoa cung cac chi so an toan IP)
export type FbRetentionMode = "latest_only" | "max_posts" | "max_days";

export interface FbTrackerSettings {
	poll_new_mins: number;
	poll_mid_mins: number;
	poll_old_mins: number;
	page_scan_mins: number;
	delay_seconds: number;
	max_batch_size: number;
	retention_mode: FbRetentionMode;
	retention_max_posts: number;
	retention_max_days: number;
	fetch_comments: boolean;
	expand_replies: boolean;
	background_task_enabled: boolean;
	custom_source_labels?: string[];
}

export interface FbPostWatchItem {
	id: string;
	url: string;
	fb_post_id?: string;
	source_type: string;
	enabled: boolean;
	auto_paused_reason?: string | null;
	from_page_id?: string;
	from_page?: string;
	from_page_name?: string;
	added_at: string;
}

export interface FbPageWatchItem {
	id: string;
	page_identifier: string;
	limit: number;
	source_type: string;
	enabled: boolean;
	added_at: string;
}

export interface FbWatchlistData {
	settings: FbTrackerSettings;
	posts: FbPostWatchItem[];
	pages: FbPageWatchItem[];
}

const WATCHLIST_PATH = ".content-pipeline/fb-watchlist.json";
const STATE_PATH = ".content-pipeline/fb-tracker-state.json";
const POST_CACHE_DIR = ".content-pipeline/fb_cache/posts";

// Cac thong so bao ve IP duoc khoa cung o muc an toan tuyet doi
const LOCKED_SAFE_SETTINGS: FbTrackerSettings = {
	poll_new_mins: 15,
	poll_mid_mins: 60,
	poll_old_mins: 360,
	page_scan_mins: 60,
	delay_seconds: 8,
	max_batch_size: 20,
	retention_mode: "max_days",
	retention_max_posts: 20,
	retention_max_days: 7,
	fetch_comments: true,
	expand_replies: false,
	background_task_enabled: false,
	custom_source_labels: [],
};

// Ham tien ich dinh tuyen dung binary Python 3.12 tren Windows Electron (tranh loi spawn .cmd)
export function resolvePythonExe(): string {
	try {
		const fs = require("fs");
		const path = require("path");
		const appData = process.env.APPDATA || "";
		const candidates = [
			path.join(appData, "uv", "python", "cpython-3.12-windows-x86_64-none", "python.exe"),
			"C:\\Users\\Admin\\AppData\\Roaming\\uv\\python\\cpython-3.12-windows-x86_64-none\\python.exe",
		];
		for (const c of candidates) {
			if (c && fs.existsSync(c)) {
				return c;
			}
		}
	} catch {
		// Fallback
	}
	return "python";
}

function sanitizeMarkdownBody(text: string): string {
	if (!text) return "";
	return text.replace(/\[\[/g, "\\[\\[").replace(/\]\]/g, "\\]\\]");
}

function formatNowVn(): string {
	const now = new Date();
	const pad = (n: number) => String(n).padStart(2, "0");
	return `${pad(now.getDate())}/${pad(now.getMonth() + 1)}/${now.getFullYear()} ${pad(now.getHours())}:${pad(now.getMinutes())}`;
}

function calcEngagementScore(m: { likes?: number; comments?: number; shares?: number }): number {
	return (m.likes || 0) * 1 + (m.comments || 0) * 2 + (m.shares || 0) * 3;
}

// Modal tao nhan Phan loai nguon moi (dong bo xuyen suot 4 bang & bieu do)
class CreateSourceLabelModal extends Modal {
	private onSubmit: (newLabel: string | null) => void;
	private submitted = false;

	constructor(app: App, onSubmit: (newLabel: string | null) => void) {
		super(app);
		this.onSubmit = onSubmit;
	}

	onOpen(): void {
		const { contentEl } = this;
		contentEl.empty();
		contentEl.addClass("content-compass-fb-preview-modal");

		const header = contentEl.createDiv({ cls: "content-compass-fb-modal-header" });
		const h3 = header.createEl("h3");
		setBtnContent(h3, "tag", "Tạo nhãn Phân loại mới");

		const box = contentEl.createDiv({ cls: "content-compass-fb-modal-savebox" });
		const lbl = box.createEl("label", { cls: "content-compass-fb-modal-field" });
		lbl.createSpan({
			text: "Tên nhãn phân loại (sẽ tự động liên kết ở tất cả các bảng và bộ lọc biểu đồ):",
		});
		const inp = lbl.createEl("input", {
			type: "text",
			placeholder: "Ví dụ: Kênh đối tác, KOLs, Cộng đồng, Nguồn tham khảo...",
		}) as HTMLInputElement;

		const actions = box.createDiv({ cls: "content-compass-fb-modal-actions" });
		const cancelBtn = actions.createEl("button", {
			cls: "content-compass-refresh-btn",
			text: "Hủy",
			attr: { type: "button" },
		});
		const saveBtn = actions.createEl("button", {
			cls: "content-compass-import-btn",
			attr: { type: "button" },
		});
		setBtnContent(saveBtn, "check", "Tạo & Chọn nhãn này");

		const submitVal = () => {
			const val = inp.value.trim();
			if (!val) return;
			this.submitted = true;
			this.onSubmit(val);
			this.close();
		};

		saveBtn.addEventListener("click", submitVal);
		cancelBtn.addEventListener("click", () => this.close());
		inp.addEventListener("keydown", (e) => {
			if (e.key === "Enter") {
				e.preventDefault();
				submitVal();
			}
		});
		window.setTimeout(() => inp.focus(), 50);
	}

	onClose(): void {
		this.contentEl.empty();
		if (!this.submitted) {
			this.onSubmit(null);
		}
	}
}

// Modal xem truoc toan van noi dung bai viet, cay binh luan va tuy chinh tieu de truoc khi luu vao Vault
class ScrapedPostModal extends Modal {
	private cacheData: any;
	private defaultSourceType: string;
	private isSaved: boolean;
	private onSaveWithCustomOpts: (customTitle: string, targetSource: string) => Promise<void>;

	constructor(
		app: App,
		cacheData: any,
		defaultSourceType: string,
		isSaved: boolean,
		onSaveWithCustomOpts: (customTitle: string, targetSource: string) => Promise<void>
	) {
		super(app);
		this.cacheData = cacheData;
		this.defaultSourceType = defaultSourceType;
		this.isSaved = isSaved;
		this.onSaveWithCustomOpts = onSaveWithCustomOpts;
	}

	onOpen(): void {
		const { contentEl } = this;
		contentEl.empty();
		contentEl.addClass("content-compass-fb-preview-modal");

		const header = contentEl.createDiv({ cls: "content-compass-fb-modal-header" });
		const h3 = header.createEl("h3");
		setBtnContent(h3, "file-text", `Nguồn: ${this.cacheData.author_name || "Facebook"}`);

		const metaRow = contentEl.createDiv({ cls: "content-compass-fb-modal-meta" });
		const m = this.cacheData.metrics || {};
		const likes = Number(m.likes || 0);
		const commentsCnt = Number(m.comments || 0);
		const shares = Number(m.shares || 0);
		const score = calcEngagementScore(m);
		const modalScoreChip = createMetricChip(metaRow, "flame", `Score ${score}`, "content-compass-fb-score-badge");
		modalScoreChip.setAttribute(
			"title",
			`Cách tính Điểm tương tác (Score):\n• Likes: ${likes} × 1 = ${likes} điểm\n• Bình luận: ${commentsCnt} × 2 = ${commentsCnt * 2} điểm\n• Chia sẻ: ${shares} × 3 = ${shares * 3} điểm\n────────────────────\nTổng cộng: ${score} điểm`
		);
		createMetricChip(metaRow, "thumbs-up", `${likes} Likes`);
		createMetricChip(metaRow, "message-circle", `${commentsCnt} Comments`);
		createMetricChip(metaRow, "share-2", `${shares} Shares`);
		createMetricChip(metaRow, "eye", `${m.views || 0} Views`);

		// Khung tuy chinh Tieu de va Thu muc luu vao Vault
		const saveConfigBox = contentEl.createDiv({ cls: "content-compass-fb-modal-savebox" });
		const rawFirstLine = String(this.cacheData.post_text || "")
			.trim()
			.split("\n")[0]
			.slice(0, 75)
			.replace(/"/g, "'");
		const defaultTitle = rawFirstLine || `Bài viết ${this.cacheData.fb_post_id || ""}`;

		const lblTitle = saveConfigBox.createEl("label", { cls: "content-compass-fb-modal-field" });
		lblTitle.createSpan({ text: "Tiêu đề bài viết khi lưu vào Vault:" });
		const inpTitle = lblTitle.createEl("input", { type: "text", value: defaultTitle }) as HTMLInputElement;

		const rowBottom = saveConfigBox.createDiv({ cls: "content-compass-fb-modal-actions" });
		const selDest = rowBottom.createEl("select", { cls: "content-compass-fb-inline-select" }) as HTMLSelectElement;
		const nonOwnType = this.defaultSourceType && this.defaultSourceType !== "own" ? this.defaultSourceType : "external";
		selDest.createEl("option", {
			value: nonOwnType,
			text: `Lưu vào: 03-Content/Viral Posts (${formatSourceTypeLabel(nonOwnType)})`,
		});
		selDest.createEl("option", { value: "own", text: "Lưu vào: 03-Content/Posted (Thương hiệu)" });
		selDest.value = this.defaultSourceType === "own" ? "own" : nonOwnType;

		const saveBtn = rowBottom.createEl("button", {
			cls: "content-compass-import-btn",
		});
		setBtnContent(saveBtn, "download", this.isSaved ? "Cập nhật lại vào Vault" : "Lưu bài viết vào Vault");
		saveBtn.addEventListener("click", async () => {
			setBtnContent(saveBtn, "loader", "Đang lưu...", true);
			saveBtn.setAttribute("disabled", "true");
			await this.onSaveWithCustomOpts(
				inpTitle.value.trim() || defaultTitle,
				selDest.value
			);
			setBtnContent(saveBtn, "check", "Đã lưu vào Vault");
		});

		const bodyBox = contentEl.createDiv({ cls: "content-compass-fb-modal-body" });
		const h4Body = bodyBox.createEl("h4");
		setBtnContent(h4Body, "align-left", "Nội dung bài viết gốc");
		const postPre = bodyBox.createDiv({ cls: "content-compass-fb-modal-text" });
		postPre.setText(this.cacheData.post_text || "(Bài viết dạng Video/Hình ảnh không có văn bản)");

		const comments: any[] = Array.isArray(this.cacheData.comments_tree) ? this.cacheData.comments_tree : [];
		const h4Comments = bodyBox.createEl("h4");
		setBtnContent(h4Comments, "message-square", `Bình luận thu thập được (${comments.length} luồng thảo luận)`);
		if (comments.length === 0) {
			bodyBox.createDiv({ cls: "content-compass-import-status", text: "Chưa có bình luận nào được thu thập." });
		} else {
			const cList = bodyBox.createDiv({ cls: "content-compass-fb-modal-comments" });
			for (const c of comments) {
				const item = cList.createDiv({ cls: "content-compass-fb-comment-item" });
				const authorName = c.author?.name || "Người dùng";
				item.createEl("strong", { text: `${authorName} (${c.reactions || 0} likes): ` });
				item.createSpan({ text: c.text || "" });

				if (Array.isArray(c.replies) && c.replies.length > 0) {
					const rList = item.createDiv({ cls: "content-compass-fb-comment-replies" });
					for (const r of c.replies) {
						const rItem = rList.createDiv({ cls: "content-compass-fb-reply-item" });
						rItem.createEl("strong", { text: `↳ ${r.author?.name || "Người dùng"} (${r.reactions || 0} likes): ` });
						rItem.createSpan({ text: r.text || "" });
					}
				}
			}
		}
	}

	onClose(): void {
		this.contentEl.empty();
	}
}

// Nhom 2: Lop ImportEngineView
export class ImportEngineView {
	private container: HTMLElement;
	private engagementStore: EngagementStore;
	private app: App;
	private onRefreshDashboard: (() => void) | null;
	// Mac dinh AN ngan keo nhap lieu de tiet kiem dien tich man hinh khi user khong dung den
	private isInputDrawerOpen: boolean = false;
	private activeSubTab: "fb" | "manual" | "csv" = "fb";
	private isAdvancedSectionOpen: boolean = true;
	private isWorkloadPanelCollapsed: boolean = false;
	private isFanpagesTableCollapsed: boolean = false;
	private isPostsTableCollapsed: boolean = false;
	private isRecentHistoryCollapsed: boolean = false;
	private selectedPostIds: Set<string> = new Set();
	private postActiveFilter: "all" | "active" | "paused" = "all";
	private postVaultFilter: "all" | "unsaved" | "saved" = "all";
	private postSourceFilter: string = "all";
	private postSortBy: "score_desc" | "comments_desc" | "shares_desc" | "recent" = "score_desc";
	private postSearchQuery: string = "";
	private postDateRange: DateRangeSelection = {
		presetId: "all",
		startDate: "",
		endDate: "",
	};
	private livePollTimer: number | null = null;
	private highlightRowTimer: number | null = null;

	constructor(
		container: HTMLElement,
		engagementStore: EngagementStore,
		app: App,
		onRefreshDashboard?: () => void
	) {
		this.container = container;
		this.engagementStore = engagementStore;
		this.app = app;
		this.onRefreshDashboard = onRefreshDashboard || null;
	}

	// Nhom 3: Render khung giao dien chinh (Header gon nhe + Ngan keo Nhap lieu An/Hien + Bang Theo doi Luon Hien thi)
	public render(): void {
		this.container.empty();
		this.renderMainView(this.container);
	}

	/**
	 * Chuyen focus, cuon muot va to sang (highlight) bai viet duoc chon tu Bieu do Engagement sang Bang Danh sach bai viet da thu thap.
	 */
	public async focusAndHighlightPost(target: TimelinePeriodPostItem): Promise<void> {
		const findRowInDom = (): HTMLElement | null => {
			const rows = Array.from(this.container.querySelectorAll("tr.cc-post-row")) as HTMLElement[];
			for (const r of rows) {
				const wId = r.getAttribute("data-watch-id") || "";
				const fbId = r.getAttribute("data-fb-id") || "";
				const slug = r.getAttribute("data-post-slug") || "";
				const url = r.getAttribute("data-post-url") || "";
				if (target.watchId && wId && wId === target.watchId) return r;
				if (target.fbPostId && fbId && fbId === target.fbPostId) return r;
				if (
					target.postId &&
					(slug === target.postId || fbId === target.postId || wId === target.postId)
				) {
					return r;
				}
				if (target.vaultSlug && slug && slug === target.vaultSlug) return r;
				if (target.url && url && url === target.url) return r;
			}
			return null;
		};

		const hasActiveDateFilter =
			this.postDateRange.presetId !== "all" ||
			Boolean(this.postDateRange.startDate) ||
			Boolean(this.postDateRange.endDate);

		if (this.isPostsTableCollapsed || hasActiveDateFilter || !findRowInDom()) {
			this.isPostsTableCollapsed = false;
			// Luôn clear bộ lọc thời gian của bảng Danh sách bài viết để chắc chắn bài viết được hiển thị mà user không cần chỉnh lại
			this.postDateRange = {
				presetId: "all",
				startDate: "",
				endDate: "",
			};
			this.postActiveFilter = "all";
			this.postVaultFilter = "all";
			this.postSourceFilter = "all";
			this.postSearchQuery = "";
			await this.renderMainView(this.container);
		}

		const targetRow = findRowInDom();
		if (!targetRow) return;

		this.container.querySelectorAll("tr.cc-post-row.is-highlighted-target").forEach((el) => {
			el.removeClass("is-highlighted-target");
		});
		if (this.highlightRowTimer) {
			window.clearTimeout(this.highlightRowTimer);
			this.highlightRowTimer = null;
		}

		targetRow.addClass("is-highlighted-target");
		targetRow.scrollIntoView({ behavior: "smooth", block: "center" });

		this.highlightRowTimer = window.setTimeout(() => {
			targetRow.removeClass("is-highlighted-target");
			this.highlightRowTimer = null;
		}, 4000);
	}

	// Nhom 4: Doc/Ghi file cau hinh Watchlist, State, Cache va Luu bai viet vao Vault
	private normalizeSettings(rawSettings: any): FbTrackerSettings {
		const modeRaw = String(rawSettings?.retention_mode || "max_days");
		const retentionMode: FbRetentionMode =
			modeRaw === "latest_only" || modeRaw === "max_posts" || modeRaw === "max_days"
				? modeRaw
				: "max_days";
		const rawLabels = Array.isArray(rawSettings?.custom_source_labels) ? rawSettings.custom_source_labels : [];
		const customLabels: string[] = Array.from(
			new Set<string>(
				rawLabels
					.map((x: any) => String(x || "").trim())
					.filter((x: string) => x.length > 0 && x !== "own" && x !== "external" && x !== "other")
			)
		);
		return {
			...LOCKED_SAFE_SETTINGS,
			max_batch_size: Math.max(1, Math.min(100, parseInt(rawSettings?.max_batch_size) || 20)),
			retention_mode: retentionMode,
			retention_max_posts: Math.max(1, Math.min(500, parseInt(rawSettings?.retention_max_posts) || 20)),
			retention_max_days: Math.max(1, Math.min(365, parseInt(rawSettings?.retention_max_days) || 7)),
			expand_replies: Boolean(rawSettings?.expand_replies),
			background_task_enabled: Boolean(rawSettings?.background_task_enabled),
			custom_source_labels: customLabels,
		};
	}

	private collectAllCustomLabels(watchlist: FbWatchlistData): string[] {
		const set = new Set<string>();
		const pushIfCustom = (raw?: string) => {
			const s = String(raw || "").trim();
			if (s && s !== "own" && s !== "external" && s !== "other") {
				set.add(s);
			}
		};
		for (const lbl of watchlist.settings.custom_source_labels || []) {
			pushIfCustom(lbl);
		}
		for (const pg of watchlist.pages || []) {
			pushIfCustom(pg.source_type);
		}
		for (const pt of watchlist.posts || []) {
			pushIfCustom(pt.source_type);
		}
		for (const lbl of this.engagementStore.getCustomSourceLabels()) {
			pushIfCustom(lbl);
		}
		return Array.from(set).sort((a, b) => a.localeCompare(b, "vi"));
	}

	private bindSourceTypeSelect(
		selectEl: HTMLSelectElement,
		watchlist: FbWatchlistData,
		initialValue: string,
		onValueChanged?: (newVal: string, createdNewLabel: boolean) => Promise<void> | void
	): void {
		let currentVal = initialValue || "external";

		const populate = (selectedVal: string) => {
			selectEl.empty();
			selectEl.createEl("option", { value: "external", text: "Đối thủ" });
			selectEl.createEl("option", { value: "own", text: "Thương hiệu" });
			selectEl.createEl("option", { value: "other", text: "Khác" });

			const customLabels = this.collectAllCustomLabels(watchlist);
			if (
				selectedVal &&
				selectedVal !== "external" &&
				selectedVal !== "own" &&
				selectedVal !== "other" &&
				!customLabels.includes(selectedVal)
			) {
				customLabels.push(selectedVal);
			}
			for (const lbl of customLabels) {
				selectEl.createEl("option", { value: lbl, text: lbl });
			}
			selectEl.createEl("option", { value: "__create_new__", text: "+ Tạo nhãn mới..." });
			selectEl.value = selectedVal;
		};

		populate(currentVal);

		selectEl.addEventListener("change", async () => {
			if (selectEl.value === "__create_new__") {
				new CreateSourceLabelModal(this.app, async (rawNewLabel) => {
					if (!rawNewLabel) {
						selectEl.value = currentVal;
						return;
					}
					const trimmed = rawNewLabel.trim();
					let normalized = trimmed;
					const lower = trimmed.toLowerCase();
					if (lower === "thương hiệu" || lower === "own") normalized = "own";
					else if (lower === "đối thủ" || lower === "external") normalized = "external";
					else if (lower === "khác" || lower === "other") normalized = "other";

					if (normalized !== "own" && normalized !== "external" && normalized !== "other") {
						if (!Array.isArray(watchlist.settings.custom_source_labels)) {
							watchlist.settings.custom_source_labels = [];
						}
						if (!watchlist.settings.custom_source_labels.includes(normalized)) {
							watchlist.settings.custom_source_labels.push(normalized);
						}
						await this.saveWatchlist(watchlist);
					}
					currentVal = normalized;
					populate(currentVal);
					if (onValueChanged) {
						await onValueChanged(currentVal, true);
					}
				}).open();
				return;
			}

			currentVal = selectEl.value;
			if (onValueChanged) {
				await onValueChanged(currentVal, false);
			}
		});
	}

	private async loadWatchlist(): Promise<FbWatchlistData> {
		try {
			if (await this.app.vault.adapter.exists(WATCHLIST_PATH)) {
				const raw = await this.app.vault.adapter.read(WATCHLIST_PATH);
				const parsed = JSON.parse(raw);
				return {
					settings: this.normalizeSettings(parsed?.settings),
					posts: Array.isArray(parsed.posts) ? parsed.posts : [],
					pages: Array.isArray(parsed.pages) ? parsed.pages : [],
				};
			}
		} catch (e) {
			console.warn("[FacebookTracker] Không thể đọc fb-watchlist.json:", e);
		}
		return { settings: { ...LOCKED_SAFE_SETTINGS }, posts: [], pages: [] };
	}

	private async saveWatchlist(data: FbWatchlistData): Promise<void> {
		data.settings = this.normalizeSettings(data.settings);
		const dir = ".content-pipeline";
		if (!(await this.app.vault.adapter.exists(dir))) {
			await this.app.vault.adapter.mkdir(dir);
		}
		await this.app.vault.adapter.write(WATCHLIST_PATH, JSON.stringify(data, null, 2));
	}

	private async loadTrackerState(): Promise<any> {
		try {
			if (await this.app.vault.adapter.exists(STATE_PATH)) {
				const raw = await this.app.vault.adapter.read(STATE_PATH);
				const parsed = JSON.parse(raw);
				return {
					status: parsed.status || { is_running: false, progress_text: "Sẵn sàng" },
					auth_status: parsed.auth_status || { connected: false, c_user: null, circuit_broken: false },
					posts: parsed.posts || {},
					pages: parsed.pages || {},
					discovered_posts: Array.isArray(parsed.discovered_posts) ? parsed.discovered_posts : [],
					ignored_fb_ids: Array.isArray(parsed.ignored_fb_ids) ? parsed.ignored_fb_ids : [],
				};
			}
		} catch {
			// Bo qua neu file dang duoc ghi
		}
		return {
			status: { is_running: false, progress_text: "Sẵn sàng" },
			auth_status: { connected: false, c_user: null, circuit_broken: false },
			posts: {},
			pages: {},
			discovered_posts: [],
			ignored_fb_ids: [],
		};
	}

	private async saveTrackerState(state: any): Promise<void> {
		const dir = ".content-pipeline";
		if (!(await this.app.vault.adapter.exists(dir))) {
			await this.app.vault.adapter.mkdir(dir);
		}
		await this.app.vault.adapter.write(STATE_PATH, JSON.stringify(state, null, 2));
	}

	private async readPostCache(fbPostId: string): Promise<any | null> {
		if (!fbPostId) return null;
		const cachePath = `${POST_CACHE_DIR}/${fbPostId}.json`;
		try {
			if (await this.app.vault.adapter.exists(cachePath)) {
				const raw = await this.app.vault.adapter.read(cachePath);
				return JSON.parse(raw);
			}
		} catch {
			// Bo qua
		}
		return null;
	}

	private resolveExistingVaultPath(item: FbPostWatchItem, pState: any): string | null {
		if (pState?.vault_path) {
			const f = this.app.vault.getAbstractFileByPath(pState.vault_path);
			if (f instanceof TFile) return f.path;
		}
		const slug = pState?.vault_slug;
		if (slug) {
			for (const folder of ["03-Content/Posted", "03-Content/Viral Posts"]) {
				const candidate = `${folder}/${slug}.md`;
				const f = this.app.vault.getAbstractFileByPath(candidate);
				if (f instanceof TFile) return f.path;
			}
		}
		return null;
	}

	// Luu 1 bai viet da quet tu bo dem JSON thanh file Markdown chuan trong `03-Content/Posted` hoac `03-Content/Viral Posts`
	private async savePostToVault(
		item: FbPostWatchItem,
		state: any,
		customTitle?: string,
		overrideSourceType?: string
	): Promise<string | null> {
		const pState = state?.posts?.[item.id];
		const fbPostId = pState?.fb_post_id || item.fb_post_id;
		if (!fbPostId) return null;

		const cache = (await this.readPostCache(fbPostId)) || {
			fb_post_id: fbPostId,
			fb_url: item.url,
			source_type: item.source_type,
			vault_slug: pState?.vault_slug || `fb-post-${fbPostId}`,
			author_name: pState?.author_name || "Facebook",
			creation_time: pState?.creation_time,
			post_text: pState?.title_snippet || "",
			comments_tree: [],
		};

		const sourceType = overrideSourceType || item.source_type || cache.source_type || "external";
		const targetFolder = sourceType === "own" ? "03-Content/Posted" : "03-Content/Viral Posts";
		if (!(await this.app.vault.adapter.exists("03-Content"))) {
			await this.app.vault.adapter.mkdir("03-Content");
		}
		if (!(await this.app.vault.adapter.exists(targetFolder))) {
			await this.app.vault.adapter.mkdir(targetFolder);
		}

		const slug = pState?.vault_slug || cache.vault_slug || `fb-post-${fbPostId}`;
		const filePath = `${targetFolder}/${slug}.md`;

		const rawText = String(cache.post_text || "").trim();
		const safeText = sanitizeMarkdownBody(rawText);
		const authorName = sanitizeMarkdownBody(String(cache.author_name || "Facebook"));
		const pubDate = cache.creation_time
			? new Date(Number(cache.creation_time) * 1000).toISOString().split("T")[0]
			: new Date().toISOString().split("T")[0];
		const titleSnippet = (customTitle || (safeText ? safeText.split("\n")[0].slice(0, 70) : `Bài viết ${fbPostId}`))
			.replace(/"/g, "'");

		const comments: any[] = Array.isArray(cache.comments_tree) ? cache.comments_tree : [];
		let commentsBlock = "";
		if (comments.length > 0) {
			const cLines: string[] = [
				"\n## 💬 Bình luận thu thập (Threaded Comments)\n",
				`*Cập nhật lúc: ${formatNowVn()} (GMT+7)*\n`,
			];
			for (const c of comments) {
				const aName = sanitizeMarkdownBody(c.author?.name || "Người dùng");
				const aUrl = c.author?.profile_url || "#";
				const cText = sanitizeMarkdownBody(String(c.text || "").replace(/\n/g, " "));
				cLines.push(`- **[${aName}](${aUrl})** *(👍 ${c.reactions || 0})*: ${cText}`);
				if (Array.isArray(c.replies)) {
					for (const r of c.replies) {
						const rName = sanitizeMarkdownBody(r.author?.name || "Người dùng");
						const rUrl = r.author?.profile_url || "#";
						const rText = sanitizeMarkdownBody(String(r.text || "").replace(/\n/g, " "));
						cLines.push(`  - ↳ **[${rName}](${rUrl})** *(👍 ${r.reactions || 0})*: ${rText}`);
					}
				}
			}
			commentsBlock = "\n" + cLines.join("\n") + "\n";
		}

		if (await this.app.vault.adapter.exists(filePath)) {
			let existingContent = await this.app.vault.adapter.read(filePath);
			if (safeText && existingContent.includes("*(Bài viết dạng Video/Hình ảnh không có văn bản)*")) {
				existingContent = existingContent.replace("*(Bài viết dạng Video/Hình ảnh không có văn bản)*", safeText);
			}
			const marker = "\n## 💬 Bình luận thu thập (Threaded Comments)\n";
			if (existingContent.includes(marker)) {
				existingContent = existingContent.split(marker)[0].trimEnd() + "\n";
			}
			await this.app.vault.adapter.write(filePath, existingContent + commentsBlock);
		} else {
			const mdContent =
				`---\n` +
				`title: "${titleSnippet}"\n` +
				`publish_date: ${pubDate}\n` +
				`platform:\n  - facebook\n` +
				`fb_post_id: "${fbPostId}"\n` +
				`fb_url: "${item.url}"\n` +
				`author: "${authorName}"\n` +
				`source_type: ${sourceType}\n` +
				`tags: []\n` +
				`status: published\n` +
				`---\n\n` +
				`<!--\n` +
				`- Tên file: ${slug}.md\n` +
				`- Last update: ${formatNowVn()} (GMT+7)\n` +
				`- Vai trò: Lưu trữ nội dung và bình luận bài viết Facebook (${fbPostId}).\n` +
				`- Được sử dụng khi nào?: Khi phân tích nội dung và ánh xạ điểm tương tác trong Content Compass.\n` +
				`- Output: Nội dung bài viết gốc và cây bình luận phân nhánh.\n` +
				`- Tóm tắt logic hoạt động: Lưu có chọn lọc từ bộ đệm của facebook_realtime_tracker.py.\n` +
				`-->\n\n` +
				`# ${titleSnippet}\n\n` +
				`- **Nguồn:** [${authorName}](${item.url})\n` +
				`- **Ngày đăng:** ${pubDate}\n\n` +
				`## 📝 Nội dung bài viết\n\n` +
				`${safeText || "*(Bài viết dạng Video/Hình ảnh không có văn bản)*"}\n` +
				commentsBlock;

			await this.app.vault.adapter.write(filePath, mdContent);
		}

		if (state.posts && state.posts[item.id]) {
			state.posts[item.id].saved_to_vault = true;
			state.posts[item.id].vault_path = filePath;
			state.posts[item.id].vault_slug = slug;
			await this.saveTrackerState(state);
		}
		return filePath;
	}

	public triggerPythonTracker(args: string[], onDone?: () => void, liveStatusEl?: HTMLElement): void {
		try {
			const { spawn } = require("child_process");
			const path = require("path");
			const adapter = this.app.vault.adapter as any;
			const vaultPath = adapter?.basePath;
			if (!vaultPath) return;

			if (this.livePollTimer) {
				window.clearInterval(this.livePollTimer);
				this.livePollTimer = null;
			}

			if (liveStatusEl) {
				this.livePollTimer = window.setInterval(async () => {
					const st = await this.loadTrackerState();
					const prog = st?.status?.progress_text || "Đang xử lý...";
					liveStatusEl.setText(prog);
				}, 2000);
			}

			const pyExe = resolvePythonExe();
			const scriptPath = path.resolve(vaultPath, "..", ".agents", "scripts", "facebook_realtime_tracker.py");
			const child = spawn(pyExe, [scriptPath, "--vault", vaultPath, ...args], {
				windowsHide: true,
				stdio: "ignore",
			});
			child.on("close", async () => {
				if (this.livePollTimer) {
					window.clearInterval(this.livePollTimer);
					this.livePollTimer = null;
				}
				await this.engagementStore.initialize();
				if (this.onRefreshDashboard) {
					this.onRefreshDashboard();
				} else if (onDone) {
					onDone();
				}
			});
		} catch (err) {
			console.error("[FacebookTracker] Lỗi gọi tiến trình Python:", err);
		}
	}

	// Nhom 5: Giao dien chinh chuan Apple Bento Workspace (Khong long hop 4 tang, khong giat nhay DOM khi await)
	private async renderMainView(rootContainer: HTMLElement): Promise<void> {
		const scrollParent = rootContainer.closest(".content-compass-tab-content") as HTMLElement | null;
		const savedScrollTop = scrollParent ? scrollParent.scrollTop : 0;

		const watchlist = await this.loadWatchlist();
		const state = await this.loadTrackerState();
		rootContainer.empty();
		const isRunning = Boolean(state?.status?.is_running);

		const pageSourceMap = new Map<string, string>();
		for (const pg of watchlist.pages) {
			if (pg.id && pg.source_type) pageSourceMap.set(pg.id, pg.source_type);
			if (pg.page_identifier && pg.source_type) pageSourceMap.set(pg.page_identifier, pg.source_type);
		}

		const allPosts: Array<FbPostWatchItem & { isDiscovered?: boolean }> = [
			...watchlist.posts,
			...(Array.isArray(state?.discovered_posts)
				? state.discovered_posts.map((d: any) => {
						const inheritedSrc =
							(d.from_page_id && pageSourceMap.get(d.from_page_id)) ||
							(d.from_page && pageSourceMap.get(d.from_page)) ||
							d.source_type ||
							"external";
						d.source_type = inheritedSrc;
						return { ...d, source_type: inheritedSrc, isDiscovered: true };
				  })
				: []),
		];

		const workspace = rootContainer.createDiv({ cls: "content-compass-fb-workspace" });

		// 1. Thanh Glass Control Bar tren cung
		const statusBar = workspace.createDiv({ cls: "content-compass-fb-statusbar" });
		const leftStatus = statusBar.createDiv({ cls: "content-compass-fb-status-text" });
		const statusLine = leftStatus.createDiv({ cls: "content-compass-fb-status-line" });
		statusLine.createSpan({ cls: `cc-status-dot ${isRunning ? "is-running" : ""}` });

		const progressText = state?.status?.progress_text || "Sẵn sàng";
		const lastRun = state?.status?.last_run_at
			? new Date(state.status.last_run_at).toLocaleString("vi-VN")
			: "Chưa quét";
		const activePostsCount = allPosts.filter((p) => p.enabled !== false).length;
		const pausedPostsCount = allPosts.length - activePostsCount;
		const batchSizeVal = Math.max(1, watchlist.settings.max_batch_size || 20);
		const numBatchesCurrent = Math.max(1, Math.ceil(Math.max(1, activePostsCount) / batchSizeVal));
		const cycleMinsCurrent = numBatchesCurrent * (watchlist.settings.poll_new_mins || 15);
		const mainStatusLine = statusLine.createSpan({
			text: `Đang theo dõi: ${watchlist.pages.length} Nguồn Trang & ${activePostsCount} Bài đang bật quét (${pausedPostsCount} bài cũ đã ngắt / ${allPosts.length} tổng) • Chu kỳ: ~${cycleMinsCurrent} phút/vòng • ${progressText} (Cập nhật: ${lastRun})`,
		});

		if (state?.status?.last_error) {
			const errSpan = leftStatus.createDiv({ cls: "content-compass-fb-error" });
			setBtnContent(errSpan, "alert-circle", String(state.status.last_error));
		}

		const btnGroup = statusBar.createDiv({ cls: "content-compass-fb-btn-group" });

		// Nut Bat/Tat Ngan keo Thu thap, Nhap du lieu & Cai dat Quet tu dong (Mac dinh AN de tiet kiem dien tich)
		const toggleDrawerBtn = btnGroup.createEl("button", {
			cls: `content-compass-refresh-btn ${this.isInputDrawerOpen ? "is-active" : ""}`,
		});
		setBtnContent(
			toggleDrawerBtn,
			this.isInputDrawerOpen ? "chevron-up" : "plus",
			this.isInputDrawerOpen
				? "Thu gọn khung nhập liệu & cài đặt"
				: "Thêm nguồn / Cài đặt quét"
		);
		toggleDrawerBtn.setAttribute(
			"title",
			"Mở hoặc ẩn khung thêm Fanpage/Trang cá nhân, thêm Post URL, cài đặt quét nâng cao, nhập thủ công và import CSV"
		);
		toggleDrawerBtn.addEventListener("click", () => {
			this.isInputDrawerOpen = !this.isInputDrawerOpen;
			this.renderMainView(rootContainer);
		});

		const pollNowBtn = btnGroup.createEl("button", {
			cls: "content-compass-import-btn",
		});
		setBtnContent(
			pollNowBtn,
			isRunning ? "loader" : "refresh-cw",
			isRunning ? "Đang quét..." : "Quét cập nhật ngay",
			isRunning
		);
		if (isRunning) pollNowBtn.setAttribute("disabled", "true");
		pollNowBtn.addEventListener("click", () => {
			setBtnContent(pollNowBtn, "loader", "Đang quét...", true);
			pollNowBtn.setAttribute("disabled", "true");
			mainStatusLine.setText("Đang khởi tạo hàng đợi quét an toàn IP...");
			this.triggerPythonTracker(
				["--force-all"],
				() => {
					this.renderMainView(rootContainer);
				},
				mainStatusLine
			);
		});

		// 2. Ngan keo Thu thap & Nhap du lieu (CHI HIEN THI KHI USER BAM NUT MO)
		if (this.isInputDrawerOpen) {
			this.renderCollapsibleInputDrawer(workspace, watchlist, state, rootContainer, mainStatusLine);
		}

		// 3. Hai the phan vung độc lập chuẩn Apple Inset Grouped Card (LUON HIEN THI)
		this.renderWatchedFanpagesTable(workspace, watchlist, state, rootContainer, mainStatusLine);
		this.renderWatchedPostsTable(workspace, watchlist, state, allPosts, rootContainer, mainStatusLine);

		if (scrollParent) {
			scrollParent.scrollTop = savedScrollTop;
		}
	}

	// Ngan keo Nhap lieu & Cai dat Quet tu dong (Mac dinh An, chua 3 tab UISegmentedControl)
	private renderCollapsibleInputDrawer(
		workspace: HTMLElement,
		watchlist: FbWatchlistData,
		state: any,
		rootContainer: HTMLElement,
		liveStatusEl: HTMLElement
	): void {
		const drawer = workspace.createDiv({ cls: "content-compass-fb-settings-panel" });

		const tabBar = drawer.createDiv({ cls: "content-compass-import-tabs" });
		const tabFb = tabBar.createEl("button", {
			cls: `content-compass-tab-btn ${this.activeSubTab === "fb" ? "is-active" : ""}`,
		});
		setBtnContent(tabFb, "globe", "Quét tự động Facebook (Fanpage / Cá nhân / Post URL)");

		const tabManual = tabBar.createEl("button", {
			cls: `content-compass-tab-btn ${this.activeSubTab === "manual" ? "is-active" : ""}`,
		});
		setBtnContent(tabManual, "edit-3", "Nhập Engagement thủ công");

		const tabCsv = tabBar.createEl("button", {
			cls: `content-compass-tab-btn ${this.activeSubTab === "csv" ? "is-active" : ""}`,
		});
		setBtnContent(tabCsv, "file-spreadsheet", "Import CSV");

		const drawerBody = drawer.createDiv();

		const switchSubTab = (tab: "fb" | "manual" | "csv") => {
			this.activeSubTab = tab;
			tabFb.toggleClass("is-active", tab === "fb");
			tabManual.toggleClass("is-active", tab === "manual");
			tabCsv.toggleClass("is-active", tab === "csv");
			if (tab === "fb") {
				this.renderFbAddFormsInDrawer(drawerBody, watchlist, state, rootContainer, liveStatusEl);
			} else if (tab === "manual") {
				this.renderManualForm(drawerBody);
				this.renderRecentHistory(drawerBody);
			} else {
				this.renderCsvForm(drawerBody);
				this.renderRecentHistory(drawerBody);
			}
		};

		tabFb.addEventListener("click", () => switchSubTab("fb"));
		tabManual.addEventListener("click", () => switchSubTab("manual"));
		tabCsv.addEventListener("click", () => switchSubTab("csv"));

		switchSubTab(this.activeSubTab);
	}

	// Tab 1: Quet tu dong Facebook (Tich hop Them Fanpage/Trang ca nhan, Post URL, Bang Du bao Chu ky Cap nhat & Cai dat Quet nang cao)
	private renderFbAddFormsInDrawer(
		container: HTMLElement,
		watchlist: FbWatchlistData,
		state: any,
		rootContainer: HTMLElement,
		liveStatusEl: HTMLElement
	): void {
		container.empty();

		// Hang cong tac Apple UISwitch: Chay ngam, Lay binh luan cap 2 & Ket noi Nick FB phu
		const toggleRow = container.createDiv({ cls: "content-compass-fb-checkbox-row" });

		const leftToggles = toggleRow.createDiv({ cls: "content-compass-fb-btn-group" });
		const lblBgTask = leftToggles.createEl("label", { cls: "content-compass-filter-label" });
		const chkBgTask = lblBgTask.createEl("input", {
			type: "checkbox",
			cls: "content-compass-switch",
		}) as HTMLInputElement;
		chkBgTask.checked = watchlist.settings.background_task_enabled;
		lblBgTask.createSpan({ text: "Chạy ngầm tự động kể cả khi đóng Obsidian" });
		chkBgTask.addEventListener("change", async () => {
			watchlist.settings.background_task_enabled = chkBgTask.checked;
			await this.saveWatchlist(watchlist);
			this.triggerPythonTracker(
				[chkBgTask.checked ? "--register-task" : "--unregister-task"],
				() => this.renderMainView(rootContainer),
				liveStatusEl
			);
		});

		const lblReplies = leftToggles.createEl("label", { cls: "content-compass-filter-label" });
		const chkReplies = lblReplies.createEl("input", {
			type: "checkbox",
			cls: "content-compass-switch",
		}) as HTMLInputElement;
		chkReplies.checked = watchlist.settings.expand_replies;
		lblReplies.createSpan({ text: "Lấy cả bình luận trả lời cấp 2 (Sub-replies)" });
		chkReplies.addEventListener("change", async () => {
			watchlist.settings.expand_replies = chkReplies.checked;
			await this.saveWatchlist(watchlist);
		});

		// Cum nut Ket noi Nick FB phu (Phuong an B - Mo cua so Chrome cach ly)
		const rightAuth = toggleRow.createDiv({ cls: "content-compass-fb-btn-group" });
		const authSt = state?.auth_status || {};
		if (authSt.connected && authSt.c_user) {
			const pill = rightAuth.createSpan({ cls: "content-compass-fb-auth-pill" });
			pill.createSpan({ cls: "cc-status-dot" });
			pill.createSpan({ text: `FB phụ đã kết nối (${authSt.c_user})` });

			const btnLogout = rightAuth.createEl("button", {
				cls: "content-compass-refresh-btn",
			});
			setBtnContent(btnLogout, "log-out", "Gỡ kết nối");
			btnLogout.setAttribute("title", "Xóa Cookie nick phụ và quay về chế độ 100% Không Cookie");
			btnLogout.addEventListener("click", () => {
				setBtnContent(btnLogout, "loader", "Đang gỡ...", true);
				this.triggerPythonTracker(["--logout-auth"], () => this.renderMainView(rootContainer), liveStatusEl);
			});
		} else {
			const btnLoginAuth = rightAuth.createEl("button", {
				cls: "content-compass-refresh-btn",
			});
			setBtnContent(
				btnLoginAuth,
				"key-round",
				authSt.circuit_broken
					? "Đăng nhập lại FB phụ (Phiên cũ hết hạn)"
					: "Đăng nhập FB phụ (Quét trang cá nhân)"
			);
			btnLoginAuth.setAttribute(
				"title",
				"Mở cửa sổ Chrome riêng biệt (cách ly 100% với nick chính) để đăng nhập nick phụ. Chỉ dùng khi cần quét tự động các Facebook cá nhân khóa khách ẩn danh (như my.van.7902)."
			);
			btnLoginAuth.addEventListener("click", () => {
				setBtnContent(btnLoginAuth, "loader", "Đang đợi đăng nhập trên Chrome...", true);
				btnLoginAuth.setAttribute("disabled", "true");
				this.triggerPythonTracker(["--login-auth"], () => this.renderMainView(rootContainer), liveStatusEl);
			});
		}

		const twoFormsGrid = container.createDiv({ cls: "content-compass-fb-split-form" });

		// Cột trái: Thêm Fanpage / Trang cá nhân chỉ định
		const pageBox = twoFormsGrid.createDiv({ cls: "content-compass-fb-add-box" });
		const pageSub = pageBox.createDiv({ cls: "content-compass-card-subtitle" });
		setBtnContent(pageSub, "users", "Thêm Fanpage / Trang cá nhân Facebook cần theo dõi");

		const lblPages = pageBox.createEl("label", { cls: "content-compass-fb-textarea-label" });
		lblPages.createSpan({ text: "Link Fanpage hoặc Trang cá nhân Facebook (mỗi dòng 1 địa chỉ):" });
		const txtPages = lblPages.createEl("textarea", {
			attr: {
				rows: "2",
				placeholder: "https://www.facebook.com/share/1BdsZPSQZa/\nhttps://www.facebook.com/TenFanpageHoacCaNhan",
			},
		}) as HTMLTextAreaElement;

		const pageControls = pageBox.createDiv({ cls: "content-compass-fb-side-controls" });
		const lblPageSrc = pageControls.createEl("label");
		lblPageSrc.createSpan({ text: "Phân loại:" });
		const selPageSrc = lblPageSrc.createEl("select") as HTMLSelectElement;
		this.bindSourceTypeSelect(selPageSrc, watchlist, "external", async (_val, createdNew) => {
			if (createdNew) {
				await this.engagementStore.initialize();
				if (this.onRefreshDashboard) this.onRefreshDashboard();
			}
		});

		const lblLimit = pageControls.createEl("label");
		lblLimit.createSpan({ text: "Số bài muốn quét/trang (1 - 20):" });
		const inpLimit = lblLimit.createEl("input", { type: "number", value: "5" }) as HTMLInputElement;
		inpLimit.min = "1";
		inpLimit.max = "20";

		const addPageBtn = pageControls.createEl("button", {
			cls: "content-compass-import-btn",
		});
		setBtnContent(addPageBtn, "plus", "Thêm nguồn & Quét bài mới");
		const pageMsg = pageBox.createDiv({ cls: "content-compass-import-status" });

		addPageBtn.addEventListener("click", async () => {
			const lines = txtPages.value
				.split("\n")
				.map((l) => l.trim())
				.filter((l) => l.length > 0);
			if (lines.length === 0) {
				pageMsg.setText("Vui lòng nhập ít nhất 1 địa chỉ Fanpage hoặc Trang cá nhân.");
				return;
			}
			const limit = Math.max(1, Math.min(20, parseInt(inpLimit.value) || 5));
			const sourceType = selPageSrc.value || "external";
			let lastAddedId = "";
			for (const rawPage of lines) {
				const exists = watchlist.pages.some((p) => p.page_identifier.toLowerCase() === rawPage.toLowerCase());
				if (!exists) {
					lastAddedId = `page_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;
					watchlist.pages.push({
						id: lastAddedId,
						page_identifier: rawPage,
						limit,
						source_type: sourceType,
						enabled: true,
						added_at: new Date().toISOString(),
					});
				}
			}
			await this.saveWatchlist(watchlist);
			addPageBtn.setAttribute("disabled", "true");
			pageMsg.setText(`Đã thêm ${lines.length} nguồn. Đang quét...`);
			txtPages.value = "";
			const args = lines.length === 1 && lastAddedId ? ["--force-id", lastAddedId] : ["--force-all"];
			this.triggerPythonTracker(args, () => this.renderMainView(rootContainer), liveStatusEl);
		});

		// Cột phải: Thêm Post URL chỉ định
		const postBox = twoFormsGrid.createDiv({ cls: "content-compass-fb-add-box" });
		const postSub = postBox.createDiv({ cls: "content-compass-card-subtitle" });
		setBtnContent(postSub, "link", "Thêm Post URL lẻ cần theo dõi");

		const lblUrls = postBox.createEl("label", { cls: "content-compass-fb-textarea-label" });
		lblUrls.createSpan({ text: "Dán 1 hoặc nhiều URL bài viết / Reel / Video (mỗi dòng 1 link):" });
		const txtUrls = lblUrls.createEl("textarea", {
			attr: { rows: "2", placeholder: "https://www.facebook.com/share/p/...\nhttps://www.facebook.com/reel/..." },
		}) as HTMLTextAreaElement;

		const postControls = postBox.createDiv({ cls: "content-compass-fb-side-controls" });
		const lblPostSrc = postControls.createEl("label");
		lblPostSrc.createSpan({ text: "Phân loại:" });
		const selPostSrc = lblPostSrc.createEl("select") as HTMLSelectElement;
		this.bindSourceTypeSelect(selPostSrc, watchlist, "external", async (_val, createdNew) => {
			if (createdNew) {
				await this.engagementStore.initialize();
				if (this.onRefreshDashboard) this.onRefreshDashboard();
			}
		});

		const addUrlBtn = postControls.createEl("button", {
			cls: "content-compass-import-btn",
		});
		setBtnContent(addUrlBtn, "plus", "Thêm Post URL & Quét ngay");
		const postMsg = postBox.createDiv({ cls: "content-compass-import-status" });

		addUrlBtn.addEventListener("click", async () => {
			const urls = txtUrls.value
				.split("\n")
				.map((u) => u.trim())
				.filter((u) => u.length > 0);
			if (urls.length === 0) {
				postMsg.setText("Vui lòng dán ít nhất 1 đường link bài viết.");
				return;
			}
			const sourceType = selPostSrc.value || "external";
			let lastId = "";
			for (const rawUrl of urls) {
				const exists = watchlist.posts.some((p) => p.url === rawUrl);
				if (!exists) {
					lastId = `post_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;
					watchlist.posts.push({
						id: lastId,
						url: rawUrl,
						source_type: sourceType,
						enabled: true,
						added_at: new Date().toISOString(),
					});
				}
			}
			await this.saveWatchlist(watchlist);
			addUrlBtn.setAttribute("disabled", "true");
			postMsg.setText(`Đã thêm ${urls.length} bài viết. Đang quét dữ liệu...`);
			txtUrls.value = "";
			const args = urls.length === 1 && lastId ? ["--force-id", lastId] : ["--force-all"];
			this.triggerPythonTracker(args, () => this.renderMainView(rootContainer), liveStatusEl);
		});

		// 3. BANG DU BAO KHOI LUONG THEO DOI & CHU KY CAP NHAT CHI SO TUONG TAC (HIEN THI TRUC DIEN NGAY DUOI 2 O NHAP)
		const workloadPanel = container.createDiv({
			cls: `cc-adv-workload-panel ${this.isWorkloadPanelCollapsed ? "is-collapsed" : ""}`,
		});
		const workloadHeader = workloadPanel.createDiv({ cls: "cc-adv-workload-header" });
		const workloadTitle = workloadHeader.createDiv({ cls: "content-compass-card-subtitle cc-collapsible-title" });
		const workloadBody = workloadPanel.createDiv({ cls: "cc-card-collapsible-body" });
		if (this.isWorkloadPanelCollapsed) {
			workloadBody.style.display = "none";
		}
		const syncWorkloadTitle = () => {
			setBtnContent(
				workloadTitle,
				this.isWorkloadPanelCollapsed ? "chevron-right" : "chevron-down",
				"Dự báo Khối lượng Theo dõi & Chu kỳ Cập nhật Chỉ số Tương tác (Tự động tính khi bạn nhập thêm)"
			);
			workloadTitle.setAttribute(
				"title",
				this.isWorkloadPanelCollapsed ? "Bấm để Hiện bảng" : "Bấm để Ẩn bảng"
			);
		};
		syncWorkloadTitle();
		workloadTitle.addEventListener("click", () => {
			this.isWorkloadPanelCollapsed = !this.isWorkloadPanelCollapsed;
			workloadPanel.toggleClass("is-collapsed", this.isWorkloadPanelCollapsed);
			workloadBody.style.display = this.isWorkloadPanelCollapsed ? "none" : "";
			syncWorkloadTitle();
		});

		const kpiStrip = workloadBody.createDiv({ cls: "cc-adv-kpi-strip" });
		const estimateBanner = workloadBody.createDiv({ cls: "cc-adv-estimate-banner" });

		// 4. KHOI CAI DAT QUET NANG CAO & NGUONG TU DONG NGUNG QUET CHO BAI CU (NAM TRONG CUNG TAB QUET TU DONG)
		const advWrapper = container.createDiv({ cls: "cc-adv-collapsible-section" });
		const advHeaderBar = advWrapper.createDiv({ cls: "cc-adv-section-toggle-bar" });
		const advTitleLeft = advHeaderBar.createDiv({ cls: "content-compass-card-subtitle cc-collapsible-title" });
		const syncAdvToggleBtn = () => {
			setBtnContent(
				advTitleLeft,
				this.isAdvancedSectionOpen ? "chevron-down" : "chevron-right",
				"Cài đặt Quét nâng cao & Ngưỡng tự động ngừng quét cho bài cũ"
			);
			advTitleLeft.setAttribute(
				"title",
				this.isAdvancedSectionOpen ? "Bấm để Ẩn bảng" : "Bấm để Hiện bảng"
			);
		};
		syncAdvToggleBtn();

		const advBody = advWrapper.createDiv({ cls: "cc-adv-section-body" });
		if (!this.isAdvancedSectionOpen) {
			advBody.style.display = "none";
		}
		advHeaderBar.addEventListener("click", (ev) => {
			if ((ev.target as HTMLElement).closest("input, select")) return;
			this.isAdvancedSectionOpen = !this.isAdvancedSectionOpen;
			advBody.style.display = this.isAdvancedSectionOpen ? "" : "none";
			syncAdvToggleBtn();
		});

		const splitGrid = advBody.createDiv({ cls: "content-compass-fb-split-form" });

		// --- COT TRAI: NGUONG TU DONG NGUNG QUET CHO BAI CU (3 LUA CHON) ---
		const leftBox = splitGrid.createDiv({ cls: "content-compass-fb-add-box" });
		const leftTitle = leftBox.createDiv({ cls: "content-compass-card-subtitle" });
		setBtnContent(leftTitle, "filter", "1. Ngưỡng tự động ngừng quét cho bài cũ");

		leftBox.createDiv({
			cls: "content-compass-fb-subtext",
			text: "Khi bài viết cũ vượt quá ngưỡng bên dưới, hệ thống tự động chuyển bài đó sang trạng thái Tạm dừng quét (vẫn giữ nguyên 100% số liệu lịch sử trên biểu đồ).",
		});

		const radioList = leftBox.createDiv({ cls: "cc-adv-retention-list" });
		let currentMode: FbRetentionMode = watchlist.settings.retention_mode || "max_days";

		// Lựa chọn (1): Chỉ quét N bài mới nhất ở thời điểm quét (không cộng dồn bài cũ)
		const cardOpt1 = radioList.createDiv({
			cls: `cc-adv-radio-card ${currentMode === "latest_only" ? "is-selected" : ""}`,
		});
		const rowOpt1 = cardOpt1.createEl("label", { cls: "cc-adv-radio-label" });
		const rad1 = rowOpt1.createEl("input", {
			attr: { type: "radio", name: "cc_retention_mode", value: "latest_only" },
		}) as HTMLInputElement;
		rad1.checked = currentMode === "latest_only";
		const txt1 = rowOpt1.createDiv({ cls: "cc-adv-radio-text" });
		txt1.createDiv({
			cls: "cc-adv-radio-title",
			text: "(1) Chỉ quét N bài mới nhất ở thời điểm quét (Không cộng dồn)",
		});
		txt1.createDiv({
			cls: "cc-adv-radio-desc",
			text: "Mỗi Trang chỉ giữ quét đúng N bài mới nhất trên đầu trang (theo cột 'Số bài mới/lần', mặc định 5 bài). Bài cũ hơn tự động dừng quét.",
		});

		// Lựa chọn (2): Quét cộng dồn tối đa X bài
		const cardOpt2 = radioList.createDiv({
			cls: `cc-adv-radio-card ${currentMode === "max_posts" ? "is-selected" : ""}`,
		});
		const rowOpt2 = cardOpt2.createEl("label", { cls: "cc-adv-radio-label" });
		const rad2 = rowOpt2.createEl("input", {
			attr: { type: "radio", name: "cc_retention_mode", value: "max_posts" },
		}) as HTMLInputElement;
		rad2.checked = currentMode === "max_posts";
		const txt2 = rowOpt2.createDiv({ cls: "cc-adv-radio-text" });
		const titleRow2 = txt2.createDiv({ cls: "cc-adv-inline-input-row" });
		titleRow2.createSpan({
			cls: "cc-adv-radio-title",
			text: "(2) Quét cộng dồn tối đa:",
		});
		const inpMaxPosts = titleRow2.createEl("input", {
			type: "number",
			cls: "content-compass-fb-inline-input",
			value: String(watchlist.settings.retention_max_posts || 20),
		}) as HTMLInputElement;
		inpMaxPosts.min = "1";
		inpMaxPosts.max = "500";
		titleRow2.createSpan({ cls: "cc-adv-radio-title", text: "bài viết mới nhất" });
		txt2.createDiv({
			cls: "cc-adv-radio-desc",
			text: "Cộng dồn bài mới qua các ngày nhưng giới hạn tổng số bài đang bật quét không vượt quá con số này.",
		});

		// Lựa chọn (3): Quét cộng dồn nhưng chỉ quét bài cách thời điểm quét X ngày
		const cardOpt3 = radioList.createDiv({
			cls: `cc-adv-radio-card ${currentMode === "max_days" ? "is-selected" : ""}`,
		});
		const rowOpt3 = cardOpt3.createEl("label", { cls: "cc-adv-radio-label" });
		const rad3 = rowOpt3.createEl("input", {
			attr: { type: "radio", name: "cc_retention_mode", value: "max_days" },
		}) as HTMLInputElement;
		rad3.checked = currentMode === "max_days";
		const txt3 = rowOpt3.createDiv({ cls: "cc-adv-radio-text" });
		const titleRow3 = txt3.createDiv({ cls: "cc-adv-inline-input-row" });
		titleRow3.createSpan({
			cls: "cc-adv-radio-title",
			text: "(3) Quét cộng dồn bài đăng trong vòng:",
		});
		const inpMaxDays = titleRow3.createEl("input", {
			type: "number",
			cls: "content-compass-fb-inline-input",
			value: String(watchlist.settings.retention_max_days || 7),
		}) as HTMLInputElement;
		inpMaxDays.min = "1";
		inpMaxDays.max = "365";
		titleRow3.createSpan({ cls: "cc-adv-radio-title", text: "ngày gần nhất" });
		txt3.createDiv({
			cls: "cc-adv-radio-desc",
			text: "Cộng dồn bài mới qua các ngày, tự động ngừng quét các bài đã đăng quá số ngày quy định.",
		});

		const retentionStatusMsg = leftBox.createDiv({ cls: "content-compass-import-status" });

		// --- COT PHAI: SETTING QUET NANG CAO (1 O NHAP + 6 CHI SO KHOA CUNG) ---
		const rightBox = splitGrid.createDiv({ cls: "content-compass-fb-add-box" });
		const rightTitle = rightBox.createDiv({ cls: "content-compass-card-subtitle" });
		setBtnContent(rightTitle, "shield", "2. Cài đặt Quét nâng cao & Bảo vệ IP");

		// Ô duy nhất cho phép User chỉnh sửa: Số bài quét tối đa cùng lúc trong 1 phiên
		const batchEditRow = rightBox.createDiv({ cls: "cc-adv-batch-edit-box" });
		const batchLblWrap = batchEditRow.createDiv({ cls: "cc-adv-batch-label-wrap" });
		batchLblWrap.createDiv({
			cls: "cc-adv-batch-title",
			text: "Số bài quét tối đa trong 1 phiên (Batch Size):",
		});
		batchLblWrap.createDiv({
			cls: "cc-adv-batch-sub",
			text: "Thông số duy nhất được phép tùy chỉnh (1 – 100 bài). Khuyến nghị an toàn: 15 – 25 bài.",
		});

		const inpBatchSize = batchEditRow.createEl("input", {
			type: "number",
			cls: "content-compass-fb-inline-input cc-adv-batch-input",
			value: String(watchlist.settings.max_batch_size || 20),
		}) as HTMLInputElement;
		inpBatchSize.min = "1";
		inpBatchSize.max = "100";

		// Lưới 6 chỉ số kỹ thuật hiển thị công khai nhưng KHÓA CỨNG (Read-only Locked)
		const lockedGrid = rightBox.createDiv({ cls: "cc-adv-locked-grid" });
		const lockedMetrics: Array<{ label: string; value: string; note: string }> = [
			{
				label: "Tốc độ quét (Không Cookie)",
				value: `${watchlist.settings.delay_seconds} giây / bài`,
				note: "~6 bài/phút (Khóa bảo vệ IP)",
			},
			{
				label: "Tốc độ quét (Có Cookie FB phụ)",
				value: "15 – 22 giây / bài",
				note: "Khóa chống Checkpoint nick",
			},
			{
				label: "Tần suất quét bài mới (< 12h)",
				value: `${watchlist.settings.poll_new_mins} phút / lần`,
				note: "Bắt nhịp viral đầu tiên",
			},
			{
				label: "Tần suất quét bài vừa (12 – 48h)",
				value: `${watchlist.settings.poll_mid_mins} phút / lần`,
				note: "Theo dõi ổn định",
			},
			{
				label: "Tần suất quét bài cũ (> 48h)",
				value: `${watchlist.settings.poll_old_mins} phút (6 giờ)`,
				note: "Giãn lịch tiết kiệm tài nguyên",
			},
			{
				label: "Chu kỳ quét bài mới trên Trang",
				value: `${watchlist.settings.page_scan_mins} phút / lần`,
				note: "Kiểm tra bài đăng mới",
			},
		];

		for (const lm of lockedMetrics) {
			const cell = lockedGrid.createDiv({ cls: "cc-adv-locked-item" });
			const top = cell.createDiv({ cls: "cc-adv-locked-top" });
			top.createSpan({ cls: "cc-adv-locked-label", text: lm.label });
			const lockIc = top.createSpan({ cls: "cc-icon cc-lock-icon" });
			setIcon(lockIc, "lock");
			lockIc.setAttribute("title", "Thông số hệ thống đã khóa cứng để bảo vệ an toàn IP và tài khoản");
			cell.createDiv({ cls: "cc-adv-locked-val", text: lm.value });
			cell.createDiv({ cls: "cc-adv-locked-note", text: lm.note });
		}

		// Hàm áp dụng ngay ngưỡng bài cũ trên state hiện tại và trả về số lượng bài còn bật quét
		const applyRetentionImmediately = async (saveToDisk: boolean): Promise<{
			activeCount: number;
			pausedCount: number;
			totalCount: number;
		}> => {
			watchlist.settings.retention_mode = currentMode;
			watchlist.settings.retention_max_posts = Math.max(1, Math.min(500, parseInt(inpMaxPosts.value) || 20));
			watchlist.settings.retention_max_days = Math.max(1, Math.min(365, parseInt(inpMaxDays.value) || 7));
			if (saveToDisk) {
				inpMaxPosts.value = String(watchlist.settings.retention_max_posts);
				inpMaxDays.value = String(watchlist.settings.retention_max_days);
			}

			const discovered: FbPostWatchItem[] = Array.isArray(state?.discovered_posts)
				? state.discovered_posts
				: [];
			const postsState = state?.posts || {};

			const getSortTs = (item: FbPostWatchItem): number => {
				const pst = postsState[item.id] || {};
				if (pst.creation_time) return Number(pst.creation_time) * 1000;
				if (item.added_at) {
					const t = new Date(item.added_at).getTime();
					if (!isNaN(t)) return t;
				}
				return 0;
			};

			if (currentMode === "latest_only") {
				const pageLimits = new Map<string, number>();
				for (const pg of watchlist.pages) {
					pageLimits.set(pg.id, Math.max(1, pg.limit || 5));
					pageLimits.set(pg.page_identifier, Math.max(1, pg.limit || 5));
				}
				const byPage = new Map<string, FbPostWatchItem[]>();
				for (const dp of discovered) {
					const key = dp.from_page_id || dp.from_page || "_default";
					if (!byPage.has(key)) byPage.set(key, []);
					byPage.get(key)!.push(dp);
				}
				for (const [key, list] of byPage.entries()) {
					const lim = pageLimits.get(key) || 5;
					list.sort((a, b) => getSortTs(b) - getSortTs(a));
					list.forEach((dp, idx) => {
						dp.enabled = idx < lim;
						dp.auto_paused_reason = idx < lim ? null : "latest_only";
					});
				}
			} else if (currentMode === "max_posts") {
				const allRefs: FbPostWatchItem[] = [...watchlist.posts, ...discovered];
				allRefs.sort((a, b) => getSortTs(b) - getSortTs(a));
				const maxP = watchlist.settings.retention_max_posts;
				allRefs.forEach((item, idx) => {
					if (idx >= maxP) {
						item.enabled = false;
						item.auto_paused_reason = "max_posts";
					} else if (item.auto_paused_reason) {
						item.enabled = true;
						item.auto_paused_reason = null;
					}
				});
			} else if (currentMode === "max_days") {
				const cutoffMs = Date.now() - watchlist.settings.retention_max_days * 86400000;
				const allRefs: FbPostWatchItem[] = [...watchlist.posts, ...discovered];
				for (const item of allRefs) {
					const ts = getSortTs(item);
					if (ts > 0 && ts < cutoffMs) {
						item.enabled = false;
						item.auto_paused_reason = "max_days";
					} else if (item.auto_paused_reason) {
						item.enabled = true;
						item.auto_paused_reason = null;
					}
				}
			}

			const combined = [...watchlist.posts, ...discovered];
			const activeCount = combined.filter((x) => x.enabled !== false).length;
			const totalCount = combined.length;
			const pausedCount = totalCount - activeCount;

			if (saveToDisk) {
				await this.saveWatchlist(watchlist);
				await this.saveTrackerState(state);
				retentionStatusMsg.setText(
					`Đã lưu! Hiện có ${activeCount}/${totalCount} bài đang bật quét (${pausedCount} bài cũ đã tự động tạm dừng).`
				);
			}
			return { activeCount, pausedCount, totalCount };
		};

		const formatDuration = (totalSeconds: number): string => {
			if (totalSeconds < 60) return `${Math.round(totalSeconds)} giây`;
			const mins = Math.floor(totalSeconds / 60);
			const secs = Math.round(totalSeconds % 60);
			if (mins < 60) {
				return secs > 0 ? `${mins} phút ${secs} giây` : `${mins} phút`;
			}
			const hrs = Math.floor(mins / 60);
			const remMins = mins % 60;
			return remMins > 0 ? `${hrs} giờ ${remMins} phút` : `${hrs} giờ`;
		};

		const formatCycleMins = (mins: number): string => {
			if (mins < 60) return `${mins} phút`;
			const hrs = Math.floor(mins / 60);
			const rem = mins % 60;
			return rem > 0 ? `${hrs} giờ ${rem} phút (${mins} phút)` : `${hrs} giờ (${mins} phút)`;
		};

		// Hàm tính toán & cập nhật trực tiếp Bảng Dự báo Khối lượng & Chu kỳ Cập nhật theo thời gian thực
		const updateRealtimeEstimate = async (saveNow = false) => {
			const batchVal = Math.max(1, Math.min(100, parseInt(inpBatchSize.value) || 20));
			if (saveNow) {
				inpBatchSize.value = String(batchVal);
			}
			watchlist.settings.max_batch_size = batchVal;

			const { activeCount, pausedCount, totalCount } = await applyRetentionImmediately(saveNow);
			const enabledPagesCount = watchlist.pages.filter((p) => p.enabled !== false).length;

			// Đếm số Trang mới & Bài viết mới mà User đang gõ vào 2 ô nhập liệu phía trên
			const rawPageLines = txtPages.value
				.split("\n")
				.map((l) => l.trim())
				.filter((l) => l.length > 0);
			const uniqueNewPages = rawPageLines.filter(
				(raw) => !watchlist.pages.some((p) => p.page_identifier.toLowerCase() === raw.toLowerCase())
			);
			const newPagesCount = uniqueNewPages.length;
			const limitPerNewPage = Math.max(1, Math.min(20, parseInt(inpLimit.value) || 5));
			const addedPostsFromPages = newPagesCount * limitPerNewPage;

			const rawUrlLines = txtUrls.value
				.split("\n")
				.map((u) => u.trim())
				.filter((u) => u.length > 0);
			const uniqueNewUrls = rawUrlLines.filter(
				(raw) => !watchlist.posts.some((p) => p.url.toLowerCase() === raw.toLowerCase())
			);
			const newDirectPostsCount = uniqueNewUrls.length;

			// Tổng số bài viết User đang muốn quét thêm
			const totalAddingPosts = addedPostsFromPages + newDirectPostsCount;

			// Tổng số bài viết dự kiến theo dõi sau khi cộng thêm (và áp ngưỡng nếu đang chọn chế độ 2: max_posts)
			const rawProjectedTotal = activeCount + totalAddingPosts;
			let effectiveProjectedPosts = rawProjectedTotal;
			let cappedOverflowPosts = 0;
			if (currentMode === "max_posts" && rawProjectedTotal > watchlist.settings.retention_max_posts) {
				effectiveProjectedPosts = watchlist.settings.retention_max_posts;
				cappedOverflowPosts = rawProjectedTotal - effectiveProjectedPosts;
			}
			const projectedPagesCount = enabledPagesCount + newPagesCount;

			// Số đợt (phiên) cần thiết để xoay vòng hết toàn bộ effectiveProjectedPosts bài
			const numSessionsNeeded = Math.max(1, Math.ceil(Math.max(1, effectiveProjectedPosts) / batchVal));
			const pollNewBase = watchlist.settings.poll_new_mins || 15;
			const pollMidBase = watchlist.settings.poll_mid_mins || 60;
			const pollOldBase = watchlist.settings.poll_old_mins || 360;

			// Chu kỳ xoay vòng thực tế (phút) để toàn bộ danh sách được cập nhật chỉ số mới
			const rotationCycleMins = numSessionsNeeded * pollNewBase;
			const newPostCycleMins = Math.max(pollNewBase, rotationCycleMins);
			const midPostCycleMins = Math.max(pollMidBase, rotationCycleMins);
			const oldPostCycleMins = Math.max(pollOldBase, rotationCycleMins);

			// Thời gian chạy thực tế của 1 phiên (Tầng 3 Không Cookie ~10s/bài; Tầng 2 Có Cookie ~20s/bài)
			const firstSessionPosts = Math.min(Math.max(1, effectiveProjectedPosts), batchVal);
			const secPerSessionNoCookie = projectedPagesCount * 10 + firstSessionPosts * 10;
			const secPerSessionWithCookie = projectedPagesCount * 15 + firstSessionPosts * 20;

			// Thời gian quét xong toàn bộ danh sách nếu bấm quét thủ công
			const totalManualSec =
				projectedPagesCount * 10 +
				effectiveProjectedPosts * 10 +
				(numSessionsNeeded - 1) * 120;

			// Thời gian quét lượt đầu cho số bài vừa nhập thêm
			const addingInitialBatch = Math.min(totalAddingPosts, batchVal);
			const addingInitialSec = newPagesCount * 10 + addingInitialBatch * 10;
			const addingSessions = Math.max(1, Math.ceil(Math.max(1, totalAddingPosts) / batchVal));
			const addingTotalAutoSec =
				addingSessions === 1
					? addingInitialSec
					: (addingSessions - 1) * pollNewBase * 60 +
					  (newPagesCount * 10 + (totalAddingPosts - (addingSessions - 1) * batchVal) * 10);

			// Render 4 thẻ KPI trên thanh kpiStrip
			kpiStrip.empty();

			// Thẻ 1: Đang theo dõi (quét theo lịch)
			const kpi1 = kpiStrip.createDiv({ cls: "cc-adv-kpi-box" });
			kpi1.createDiv({ cls: "cc-adv-kpi-label", text: "1. Đang theo dõi (theo lịch)" });
			kpi1.createDiv({ cls: "cc-adv-kpi-value", text: `${activeCount} bài viết` });
			kpi1.createDiv({
				cls: "cc-adv-kpi-sub",
				text: `Trên ${enabledPagesCount} Trang đang bật • Đã ngắt ${pausedCount}/${totalCount} bài cũ`,
			});

			// Thẻ 2: Đang muốn quét thêm (đang nhập ở trên)
			const kpi2 = kpiStrip.createDiv({
				cls: `cc-adv-kpi-box ${totalAddingPosts > 0 || newPagesCount > 0 ? "is-highlight" : ""}`,
			});
			kpi2.createDiv({ cls: "cc-adv-kpi-label", text: "2. Đang muốn quét thêm" });
			kpi2.createDiv({
				cls: "cc-adv-kpi-value",
				text: `+${totalAddingPosts} bài mới`,
			});
			kpi2.createDiv({
				cls: "cc-adv-kpi-sub",
				text:
					totalAddingPosts > 0 || newPagesCount > 0
						? `${newPagesCount} Trang mới (×${limitPerNewPage} bài/trang) + ${newDirectPostsCount} Post URL lẻ`
						: `Nhập link Trang (${limitPerNewPage} bài/trang) hoặc Post URL ở trên để tính`,
			});

			// Thẻ 3: Tổng số bài sẽ theo dõi theo lịch
			const kpi3 = kpiStrip.createDiv({ cls: "cc-adv-kpi-box" });
			kpi3.createDiv({ cls: "cc-adv-kpi-label", text: "3. Tổng bài sẽ quét theo lịch" });
			kpi3.createDiv({
				cls: "cc-adv-kpi-value",
				text: `${effectiveProjectedPosts} bài viết`,
			});
			kpi3.createDiv({
				cls: "cc-adv-kpi-sub",
				text:
					cappedOverflowPosts > 0
						? `Giới hạn trần ${watchlist.settings.retention_max_posts} bài (tự ngắt ${cappedOverflowPosts} bài cũ)`
						: `Hiện có ${activeCount} bài + Quét thêm ${totalAddingPosts} bài (${projectedPagesCount} Trang)`,
			});

			// Thẻ 4: Chu kỳ nhận dữ liệu tương tác mới
			const kpi4 = kpiStrip.createDiv({ cls: "cc-adv-kpi-box is-cycle" });
			kpi4.createDiv({ cls: "cc-adv-kpi-label", text: "4. Chu kỳ nhận dữ liệu mới" });
			kpi4.createDiv({
				cls: "cc-adv-kpi-value",
				text: `Mỗi ~${formatCycleMins(rotationCycleMins)}`,
			});
			kpi4.createDiv({
				cls: "cc-adv-kpi-sub",
				text: `Xoay vòng ${numSessionsNeeded} đợt × tối đa ${batchVal} bài/đợt`,
			});

			// Render khung diễn giải chi tiết & khuyến nghị an toàn
			estimateBanner.empty();
			estimateBanner.removeClass("is-safe", "is-warn", "is-danger");

			let tierClass = "is-safe";
			let badgeText = "NGƯỠNG AN TOÀN TUYỆT ĐỐI (1 – 25 BÀI/PHIÊN)";
			let bestActionText =
				"Khuyến nghị tốt nhất: Giữ mức 15 – 25 bài/phiên và bật 'Chạy ngầm tự động'. Hệ thống tự động chia nhỏ tổng số bài cần quét thành các đợt cách nhau 15 phút — an toàn 100% trên mạng thường, KHÔNG cần bật Proxy/VPN mà vẫn lấy đủ toàn bộ kết quả.";

			if (batchVal > 25 && batchVal <= 50) {
				tierClass = "is-warn";
				badgeText = "NGƯỠNG TRUNG BÌNH - CẢNH BÁO TẦN SUẤT (26 – 50 BÀI/PHIÊN)";
				bestActionText =
					"Khuyến nghị tốt nhất: Phù hợp khi bạn bấm 'Quét cập nhật ngay' thủ công 1 lần để lấy nhanh 30–50 bài. Để tránh bị Facebook chặn IP tạm thời, KHÔNG bấm quét liên tiếp quá 2 lần trong 1 giờ; nếu cần quét liên tục nhiều đợt nên bật VPN/Proxy.";
			} else if (batchVal > 50) {
				tierClass = "is-danger";
				badgeText = "NGƯỠNG RỦI RO CHẶN IP CAO (> 50 BÀI/PHIÊN)";
				bestActionText =
					"Khuyến nghị tốt nhất: Trên 1 IP mạng thường, tường lửa Facebook thường cắt kết nối (HTTP 429) ở bài thứ 45–55. Để lấy đủ kết quả an toàn: (Cách 1 - Khuyên dùng) Hạ Số bài/phiên về 20 bài để hệ thống tự chia thành nhiều đợt chạy ngầm; HOẶC (Cách 2) Bắt buộc bật VPN / đổi Proxy sang IP mới trước khi quét. Lưu ý: Tuyệt đối KHÔNG dùng Cookie tài khoản FB để tăng số lượng bài quét (Cookie chỉ dùng mở khóa trang cá nhân riêng tư).";
			}

			estimateBanner.addClass(tierClass);

			const headLine = estimateBanner.createDiv({ cls: "cc-adv-estimate-head" });
			headLine.createSpan({ text: badgeText });

			const statsList = estimateBanner.createEl("ul", { cls: "cc-adv-estimate-list" });

			if (totalAddingPosts > 0 || newPagesCount > 0) {
				statsList.createEl("li", {
					text: `Thời gian lấy xong dữ liệu lượt đầu cho +${totalAddingPosts} bài mới đang nhập (${newPagesCount} Trang mới + ${newDirectPostsCount} Post lẻ): ${
						addingSessions === 1
							? `Lấy xong toàn bộ ngay trong 1 đợt (~${formatDuration(addingInitialSec)}) sau khi bấm nút Thêm.`
							: `Đợt 1 lấy ngay ${addingInitialBatch} bài trong ~${formatDuration(addingInitialSec)}; toàn bộ +${totalAddingPosts} bài mới hoàn tất sau ${addingSessions} đợt (~${formatDuration(addingTotalAutoSec)}).`
					}`,
				});
			}

			statsList.createEl("li", {
				text: `Chu kỳ nhận bản cập nhật chỉ số tương tác (Like, Comment, Share) mới cho tổng ${effectiveProjectedPosts} bài viết: Hệ thống chia làm ${numSessionsNeeded} đợt (${batchVal} bài/đợt, mỗi đợt chạy mất ~${formatDuration(secPerSessionNoCookie)} Không Cookie hoặc ~${formatDuration(secPerSessionWithCookie)} Có Cookie):`,
			});

			const cycleSubList = statsList.createEl("ul", { cls: "cc-adv-cycle-sublist" });
			cycleSubList.createEl("li", {
				text: `Bài mới đăng (< 12h): Nhận chỉ số tương tác mới sau mỗi ~${formatCycleMins(newPostCycleMins)}.`,
			});
			cycleSubList.createEl("li", {
				text: `Bài vừa (12 – 48h): Nhận chỉ số tương tác mới sau mỗi ~${formatCycleMins(midPostCycleMins)}.`,
			});
			cycleSubList.createEl("li", {
				text: `Bài cũ (> 48h): Nhận chỉ số tương tác mới sau mỗi ~${formatCycleMins(oldPostCycleMins)}.`,
			});
			cycleSubList.createEl("li", {
				text: `Phát hiện bài mới đăng trên ${projectedPagesCount} Nguồn Trang: Tự động kiểm tra sau mỗi ${watchlist.settings.page_scan_mins} phút.${
					effectiveProjectedPosts > 0
						? ` (Nếu bấm 'Quét cập nhật ngay' thủ công cho toàn bộ ${effectiveProjectedPosts} bài: mất tổng cộng ~${formatDuration(totalManualSec)}).`
						: ""
				}`,
			});

			const guideBox = estimateBanner.createDiv({ cls: "cc-adv-estimate-guide" });
			guideBox.setText(bestActionText);
		};

		// Gắn sự kiện cập nhật tức thời khi user gõ thêm Trang, đổi số bài/trang, hoặc gõ thêm Post URL
		txtPages.addEventListener("input", () => updateRealtimeEstimate(false));
		inpLimit.addEventListener("input", () => updateRealtimeEstimate(false));
		inpLimit.addEventListener("change", () => updateRealtimeEstimate(false));
		txtUrls.addEventListener("input", () => updateRealtimeEstimate(false));

		// Gắn sự kiện cập nhật tức thời khi user đổi chế độ Ngưỡng bài cũ hoặc gõ Batch Size
		const onRetentionInputChange = () => {
			if (rad1.checked) currentMode = "latest_only";
			else if (rad2.checked) currentMode = "max_posts";
			else if (rad3.checked) currentMode = "max_days";

			cardOpt1.toggleClass("is-selected", currentMode === "latest_only");
			cardOpt2.toggleClass("is-selected", currentMode === "max_posts");
			cardOpt3.toggleClass("is-selected", currentMode === "max_days");
			updateRealtimeEstimate(true);
		};

		rad1.addEventListener("change", onRetentionInputChange);
		rad2.addEventListener("change", onRetentionInputChange);
		rad3.addEventListener("change", onRetentionInputChange);

		inpMaxPosts.addEventListener("focus", () => {
			rad2.checked = true;
			onRetentionInputChange();
		});
		inpMaxPosts.addEventListener("input", () => {
			rad2.checked = true;
			cardOpt1.toggleClass("is-selected", false);
			cardOpt2.toggleClass("is-selected", true);
			cardOpt3.toggleClass("is-selected", false);
			currentMode = "max_posts";
			updateRealtimeEstimate(false);
		});
		inpMaxPosts.addEventListener("change", () => {
			rad2.checked = true;
			onRetentionInputChange();
		});

		inpMaxDays.addEventListener("focus", () => {
			rad3.checked = true;
			onRetentionInputChange();
		});
		inpMaxDays.addEventListener("input", () => {
			rad3.checked = true;
			cardOpt1.toggleClass("is-selected", false);
			cardOpt2.toggleClass("is-selected", false);
			cardOpt3.toggleClass("is-selected", true);
			currentMode = "max_days";
			updateRealtimeEstimate(false);
		});
		inpMaxDays.addEventListener("change", () => {
			rad3.checked = true;
			onRetentionInputChange();
		});

		inpBatchSize.addEventListener("input", () => {
			updateRealtimeEstimate(false);
		});
		inpBatchSize.addEventListener("change", () => {
			updateRealtimeEstimate(true);
		});

		// Khởi chạy tính toán lần đầu khi mở tab
		updateRealtimeEstimate(false);
	}

	// Bang 1 (LUON HIEN THI): The phan vung Fanpage / Trang ca nhan chuan Apple Inset Grouped Card
	private renderWatchedFanpagesTable(
		wrapper: HTMLElement,
		watchlist: FbWatchlistData,
		state: any,
		rootContainer: HTMLElement,
		liveStatusEl: HTMLElement
	): void {
		const sectionCard = wrapper.createDiv({
			cls: `content-compass-fb-section-card ${this.isFanpagesTableCollapsed ? "is-collapsed" : ""}`,
		});
		const header = sectionCard.createDiv({ cls: "content-compass-fb-section-header" });
		const title = header.createDiv({ cls: "content-compass-card-subtitle cc-collapsible-title" });
		const tableBodyWrap = sectionCard.createDiv({ cls: "cc-card-collapsible-body" });
		if (this.isFanpagesTableCollapsed) {
			tableBodyWrap.style.display = "none";
		}
		const syncFanpagesTitle = () => {
			setBtnContent(
				title,
				this.isFanpagesTableCollapsed ? "chevron-right" : "chevron-down",
				`Nguồn Trang đang theo dõi (${watchlist.pages.length})`
			);
			title.setAttribute(
				"title",
				this.isFanpagesTableCollapsed ? "Bấm để Hiện bảng" : "Bấm để Ẩn bảng"
			);
		};
		syncFanpagesTitle();
		title.addEventListener("click", () => {
			this.isFanpagesTableCollapsed = !this.isFanpagesTableCollapsed;
			sectionCard.toggleClass("is-collapsed", this.isFanpagesTableCollapsed);
			tableBodyWrap.style.display = this.isFanpagesTableCollapsed ? "none" : "";
			syncFanpagesTitle();
		});

		if (watchlist.pages.length === 0) {
			const empty = tableBodyWrap.createDiv({ cls: "content-compass-placeholder" });
			empty.setText(
				"Chưa có Fanpage hoặc Trang cá nhân nào. Bấm 'Thêm nguồn / Nhập dữ liệu' ở góc trên để thêm."
			);
			return;
		}

		const scrollBox = tableBodyWrap.createDiv({ cls: "content-compass-table-scroll" });
		const pTable = scrollBox.createEl("table", { cls: "content-compass-data-table" });
		const pHead = pTable.createEl("thead").createEl("tr");
		for (const h of ["Tên Trang / Địa chỉ", "Phân loại", "Số bài mới/lần", "Lần quét cuối", "Theo dõi"]) {
			pHead.createEl("th", { text: h });
		}
		const pBody = pTable.createEl("tbody");
		for (const pg of watchlist.pages) {
			const st = state?.pages?.[pg.id] || {};
			const row = pBody.createEl("tr");

			const nameCell = row.createEl("td");
			const displayPageName = st.page_name || pg.page_identifier;
			const pageUrl = pg.page_identifier.startsWith("http")
				? pg.page_identifier
				: `https://www.facebook.com/${pg.page_identifier}`;
			const nameRow = nameCell.createDiv({ cls: "content-compass-fb-post-title-row" });
			const pageTitleLink = nameRow.createEl("a", {
				text: displayPageName,
				href: pageUrl,
				cls: "content-compass-fb-post-headline",
			});
			pageTitleLink.setAttribute("target", "_blank");
			pageTitleLink.setAttribute("rel", "noopener noreferrer");
			pageTitleLink.setAttribute("title", `Mở trên trình duyệt: ${pageUrl}`);
			if (st.page_name && st.page_name !== pg.page_identifier) {
				nameCell.createDiv({ text: pg.page_identifier, cls: "content-compass-fb-subtext" });
			}

			const srcCell = row.createEl("td");
			const rowSelSource = srcCell.createEl("select", { cls: "content-compass-fb-inline-select" }) as HTMLSelectElement;
			this.bindSourceTypeSelect(rowSelSource, watchlist, pg.source_type || "external", async (newVal) => {
				pg.source_type = newVal;
				if (Array.isArray(state?.discovered_posts)) {
					for (const d of state.discovered_posts) {
						if (d.from_page_id === pg.id || d.from_page === pg.page_identifier) {
							d.source_type = newVal;
						}
					}
				}
				await this.saveWatchlist(watchlist);
				await this.saveTrackerState(state);
				await this.engagementStore.initialize();
				if (this.onRefreshDashboard) {
					this.onRefreshDashboard();
				} else {
					this.renderMainView(rootContainer);
				}
			});

			const limitCell = row.createEl("td");
			const rowInpLimit = limitCell.createEl("input", {
				type: "number",
				cls: "content-compass-fb-inline-input",
				value: String(pg.limit || 5),
			}) as HTMLInputElement;
			rowInpLimit.min = "1";
			rowInpLimit.max = "20";
			rowInpLimit.addEventListener("change", async () => {
				pg.limit = Math.max(1, Math.min(20, parseInt(rowInpLimit.value) || 5));
				rowInpLimit.value = String(pg.limit);
				await this.saveWatchlist(watchlist);
				this.renderMainView(rootContainer);
			});

			const lastTime = st.last_polled_at ? new Date(st.last_polled_at).toLocaleTimeString("vi-VN") : "Chưa quét";
			const discInfo = st.last_discovered !== undefined ? ` (+${st.last_discovered} bài mới)` : "";
			row.createEl("td", { text: `${lastTime}${discInfo}` });

			const actTd = row.createEl("td");
			const actCell = actTd.createDiv({ cls: "content-compass-fb-row-actions" });
			const btnScan = actCell.createEl("button", { cls: "content-compass-icon-btn" });
			setBtnContent(btnScan, "refresh-cw");
			btnScan.setAttribute("title", "Quét nguồn này ngay lập tức");
			btnScan.addEventListener("click", () => {
				setBtnContent(btnScan, "loader", undefined, true);
				this.triggerPythonTracker(["--force-id", pg.id], () => this.renderMainView(rootContainer), liveStatusEl);
			});

			const btnToggle = actCell.createEl("button", {
				cls: `content-compass-icon-btn ${pg.enabled !== false ? "is-active-watch" : ""}`,
			});
			setBtnContent(btnToggle, pg.enabled !== false ? "pause" : "play");
			btnToggle.setAttribute(
				"title",
				pg.enabled !== false
					? "Đang bật theo dõi tự động nguồn này (Bấm để tạm dừng)"
					: "Đã tạm dừng (Bấm để tiếp tục tự động quét nguồn này)"
			);
			btnToggle.addEventListener("click", async () => {
				pg.enabled = !pg.enabled;
				await this.saveWatchlist(watchlist);
				this.renderMainView(rootContainer);
			});

			const btnDel = actCell.createEl("button", { cls: "content-compass-icon-btn is-danger" });
			setBtnContent(btnDel, "trash-2");
			btnDel.setAttribute("title", "Bỏ theo dõi nguồn này");
			btnDel.addEventListener("click", async () => {
				watchlist.pages = watchlist.pages.filter((x) => x.id !== pg.id);
				await this.saveWatchlist(watchlist);
				this.renderMainView(rootContainer);
			});
		}
	}

	// Bang 2 (LUON HIEN THI): The phan vung Bai viet da thu thap chuan Apple Inset Grouped Card
	private renderWatchedPostsTable(
		wrapper: HTMLElement,
		watchlist: FbWatchlistData,
		state: any,
		allPosts: Array<FbPostWatchItem & { isDiscovered?: boolean }>,
		rootContainer: HTMLElement,
		liveStatusEl: HTMLElement
	): void {
		const sectionCard = wrapper.createDiv({
			cls: `content-compass-fb-section-card ${this.isPostsTableCollapsed ? "is-collapsed" : ""}`,
		});
		const header = sectionCard.createDiv({ cls: "content-compass-fb-section-header" });
		const title = header.createDiv({ cls: "content-compass-card-subtitle cc-collapsible-title" });

		const postStatus = header.createDiv({ cls: "content-compass-import-status" });

		const enrichedPosts = allPosts.map((item) => {
			const st = state?.posts?.[item.id] || {};
			const vaultPath = this.resolveExistingVaultPath(item, st);
			const isScraped = Boolean(st.fb_post_id || item.fb_post_id);
			const m = st.last_metrics || { likes: 0, comments: 0, shares: 0, views: 0 };
			const score = calcEngagementScore(m);
			const authorName = st.author_name || item.from_page_name || item.from_page || "Facebook";
			const firstSentenceOrTitle = st.title_snippet || st.vault_slug || item.url;
			return {
				item,
				st,
				m,
				score,
				authorName,
				snippet: firstSentenceOrTitle,
				vaultPath,
				isSaved: Boolean(vaultPath),
				isScraped,
			};
		});

		// Xác định thứ hạng Score thực tế (Top 1 -> Top 5) trên toàn danh sách bài có điểm > 0
		const scoreRankMap = new Map<string, number>();
		const rankedByScore = [...enrichedPosts]
			.filter((x) => x.score > 0)
			.sort((a, b) => b.score - a.score);
		rankedByScore.forEach((ep, idx) => {
			scoreRankMap.set(ep.item.id, idx + 1);
		});

		const getFilteredAndSortedPosts = () => {
			const list = enrichedPosts.filter((ep) => {
				if (this.postActiveFilter === "active" && ep.item.enabled === false) return false;
				if (this.postActiveFilter === "paused" && ep.item.enabled !== false) return false;

				if (this.postVaultFilter === "saved" && !ep.isSaved) return false;
				if (this.postVaultFilter === "unsaved" && ep.isSaved) return false;

				if (this.postSourceFilter === "own" && ep.item.source_type !== "own") return false;
				if (this.postSourceFilter === "external" && ep.item.source_type !== "external") return false;
				if (this.postSourceFilter === "other" && ep.item.source_type !== "other") return false;
				if (
					this.postSourceFilter.startsWith("type:") &&
					ep.item.source_type !== this.postSourceFilter.slice(5)
				) {
					return false;
				}
				if (this.postSourceFilter === "direct" && ep.item.isDiscovered) return false;
				if (
					this.postSourceFilter.startsWith("page:") &&
					ep.item.from_page !== this.postSourceFilter.slice(5)
				) {
					return false;
				}

				if (
					this.postDateRange.presetId !== "all" &&
					this.postDateRange.startDate &&
					this.postDateRange.endDate
				) {
					const startMs = new Date(`${this.postDateRange.startDate}T00:00:00`).getTime();
					const endMs = new Date(`${this.postDateRange.endDate}T23:59:59.999`).getTime();
					const rawPostMs = ep.st.creation_time
						? Number(ep.st.creation_time) * 1000
						: ep.item.added_at
							? new Date(ep.item.added_at).getTime()
							: ep.st.last_polled_at
								? new Date(ep.st.last_polled_at).getTime()
								: 0;
					if (!rawPostMs || rawPostMs < startMs || rawPostMs > endMs) return false;
				}

				if (this.postSearchQuery.trim().length > 0) {
					const q = this.postSearchQuery.trim().toLowerCase();
					const hay = `${ep.snippet} ${ep.authorName} ${ep.item.url}`.toLowerCase();
					if (!hay.includes(q)) return false;
				}
				return true;
			});

			list.sort((a, b) => {
				if (this.postSortBy === "score_desc") return b.score - a.score;
				if (this.postSortBy === "comments_desc") return (b.m.comments || 0) - (a.m.comments || 0);
				if (this.postSortBy === "shares_desc") return (b.m.shares || 0) - (a.m.shares || 0);
				return (b.item.added_at || "").localeCompare(a.item.added_at || "");
			});
			return list;
		};

		// Thanh Bulk Actions gon ngay trong Header (hoac Toolbar strip)
		const bulkGroup = header.createDiv({ cls: "content-compass-fb-btn-group" });

		const selectAllBtn = bulkGroup.createEl("button", {
			cls: "content-compass-refresh-btn",
		});
		setBtnContent(selectAllBtn, "check-square", "Chọn tất cả");

		const clearSelBtn = bulkGroup.createEl("button", {
			cls: "content-compass-refresh-btn",
		});
		setBtnContent(clearSelBtn, "x", "Bỏ chọn");

		const saveSelectedBtn = bulkGroup.createEl("button", {
			cls: "content-compass-import-btn",
		});
		const deleteSelectedBtn = bulkGroup.createEl("button", {
			cls: "content-compass-refresh-btn",
		});

		const syncBulkActionButtons = () => {
			const cnt = this.selectedPostIds.size;
			setBtnContent(saveSelectedBtn, "download", `Lưu vào Vault (${cnt})`);
			setBtnContent(deleteSelectedBtn, "trash-2", `Xóa đã chọn (${cnt})`);
			if (cnt > 0) {
				saveSelectedBtn.removeAttribute("disabled");
				deleteSelectedBtn.removeAttribute("disabled");
			} else {
				saveSelectedBtn.setAttribute("disabled", "true");
				deleteSelectedBtn.setAttribute("disabled", "true");
			}
		};
		syncBulkActionButtons();

		saveSelectedBtn.addEventListener("click", async () => {
			setBtnContent(saveSelectedBtn, "loader", "Đang lưu...", true);
			saveSelectedBtn.setAttribute("disabled", "true");
			let savedCount = 0;
			for (const ep of enrichedPosts) {
				if (this.selectedPostIds.has(ep.item.id) && ep.isScraped) {
					const pathCreated = await this.savePostToVault(ep.item, state);
					if (pathCreated) savedCount++;
				}
			}
			this.selectedPostIds.clear();
			await this.engagementStore.initialize();
			postStatus.setText(`Đã lưu ${savedCount} bài viết vào Vault.`);
			this.renderMainView(rootContainer);
		});

		deleteSelectedBtn.addEventListener("click", async () => {
			const count = this.selectedPostIds.size;
			if (count === 0) return;
			for (const ep of enrichedPosts) {
				if (!this.selectedPostIds.has(ep.item.id)) continue;
				if (ep.item.isDiscovered) {
					const fbId = ep.st.fb_post_id || ep.item.fb_post_id;
					if (fbId && !state.ignored_fb_ids.includes(String(fbId))) {
						state.ignored_fb_ids.push(String(fbId));
					}
					state.discovered_posts = (state.discovered_posts || []).filter((d: any) => d.id !== ep.item.id);
					delete state.posts[ep.item.id];
				} else {
					watchlist.posts = watchlist.posts.filter((x) => x.id !== ep.item.id);
					delete state.posts[ep.item.id];
				}
			}
			this.selectedPostIds.clear();
			await this.saveWatchlist(watchlist);
			await this.saveTrackerState(state);
			postStatus.setText(`Đã xóa ${count} bài viết khỏi danh sách theo dõi.`);
			this.renderMainView(rootContainer);
		});

		const postsBodyWrap = sectionCard.createDiv({ cls: "cc-card-collapsible-body" });
		if (this.isPostsTableCollapsed) {
			postsBodyWrap.style.display = "none";
		}

		// Dai Filter Strip lien mach ben duoi Header (Khong bao gio bi huy/ve lai khi doi filter)
		const filterBar = postsBodyWrap.createDiv({ cls: "content-compass-fb-toolbar-strip" });

		const selSort = filterBar.createEl("select", { cls: "content-compass-fb-inline-select" }) as HTMLSelectElement;
		selSort.createEl("option", { value: "score_desc", text: "Sắp xếp: Điểm tương tác (Cao → Thấp)" });
		selSort.createEl("option", { value: "comments_desc", text: "Sắp xếp: Nhiều bình luận nhất" });
		selSort.createEl("option", { value: "shares_desc", text: "Sắp xếp: Nhiều chia sẻ nhất" });
		selSort.createEl("option", { value: "recent", text: "Sắp xếp: Mới thêm gần nhất" });
		selSort.value = this.postSortBy;

		const selSourceFilter = filterBar.createEl("select", { cls: "content-compass-fb-inline-select" }) as HTMLSelectElement;
		selSourceFilter.createEl("option", { value: "all", text: "Nguồn: Tất cả" });
		selSourceFilter.createEl("option", { value: "direct", text: "Chỉ định trực tiếp bằng URL" });
		selSourceFilter.createEl("option", { value: "own", text: "Chỉ bài: Thương hiệu" });
		selSourceFilter.createEl("option", { value: "external", text: "Chỉ bài: Đối thủ" });
		selSourceFilter.createEl("option", { value: "other", text: "Chỉ bài: Khác" });
		for (const customLbl of this.collectAllCustomLabels(watchlist)) {
			selSourceFilter.createEl("option", {
				value: `type:${customLbl}`,
				text: `Chỉ bài: ${customLbl}`,
			});
		}
		for (const pg of watchlist.pages) {
			const pName = state?.pages?.[pg.id]?.page_name || pg.page_identifier;
			selSourceFilter.createEl("option", {
				value: `page:${pg.page_identifier}`,
				text: `Từ Trang: ${pName}`,
			});
		}
		selSourceFilter.value = this.postSourceFilter;

		const selActiveFilter = filterBar.createEl("select", { cls: "content-compass-fb-inline-select" }) as HTMLSelectElement;
		const optActiveAll = selActiveFilter.createEl("option", { value: "all", text: "" });
		const optActiveOn = selActiveFilter.createEl("option", { value: "active", text: "" });
		const optActiveOff = selActiveFilter.createEl("option", { value: "paused", text: "" });
		selActiveFilter.value = this.postActiveFilter;

		const syncTableHeaderAndFilterCounts = () => {
			const activeCnt = enrichedPosts.filter((x) => x.item.enabled !== false).length;
			const pausedCnt = enrichedPosts.length - activeCnt;
			setBtnContent(
				title,
				this.isPostsTableCollapsed ? "chevron-right" : "chevron-down",
				`Danh sách Bài viết đã thu thập (${activeCnt} đang bật quét • ${pausedCnt} đã ngắt bài cũ / ${enrichedPosts.length} tổng)`
			);
			title.setAttribute(
				"title",
				this.isPostsTableCollapsed ? "Bấm để Hiện bảng" : "Bấm để Ẩn bảng"
			);
			optActiveAll.text = `Lịch quét: Tất cả (${enrichedPosts.length})`;
			optActiveOn.text = `Đang bật quét (${activeCnt})`;
			optActiveOff.text = `Đã ngắt / Tạm dừng (${pausedCnt})`;
		};
		syncTableHeaderAndFilterCounts();
		title.addEventListener("click", () => {
			this.isPostsTableCollapsed = !this.isPostsTableCollapsed;
			sectionCard.toggleClass("is-collapsed", this.isPostsTableCollapsed);
			postsBodyWrap.style.display = this.isPostsTableCollapsed ? "none" : "";
			syncTableHeaderAndFilterCounts();
		});

		const selVaultFilter = filterBar.createEl("select", { cls: "content-compass-fb-inline-select" }) as HTMLSelectElement;
		selVaultFilter.createEl("option", { value: "all", text: `Vault: Tất cả (${enrichedPosts.length})` });
		selVaultFilter.createEl("option", {
			value: "unsaved",
			text: `Chưa lưu (${enrichedPosts.filter((x) => !x.isSaved).length})`,
		});
		selVaultFilter.createEl("option", {
			value: "saved",
			text: `Đã lưu trong Vault (${enrichedPosts.filter((x) => x.isSaved).length})`,
		});
		selVaultFilter.value = this.postVaultFilter;

		// Bộ lọc Thời gian chuẩn 3 cột (Không hiển thị Gộp hay Mốc vì lọc trực tiếp trên danh sách bài viết)
		renderDateRangePickerButton(
			filterBar,
			this.postDateRange,
			{ showGroupBy: false, showDateBasis: false },
			(nextRange) => {
				this.postDateRange = nextRange;
				rebuildTableRows();
			}
		);

		const searchBox = filterBar.createDiv({ cls: "content-compass-search-box" });
		const searchIcon = searchBox.createSpan({ cls: "cc-icon" });
		setIcon(searchIcon, "search");
		const inpSearch = searchBox.createEl("input", {
			type: "text",
			cls: "content-compass-fb-search-input",
			placeholder: "Tìm theo tên bài, câu đầu tiên hoặc tác giả...",
			value: this.postSearchQuery,
		}) as HTMLInputElement;

		// Khung cuộn bảng cố định chiều cao để bảng không bao giờ bị co giãn/nhảy trang khi lọc
		const postSec = postsBodyWrap.createDiv({ cls: "content-compass-table-scroll content-compass-posts-scroll" });
		const table = postSec.createEl("table", { cls: "content-compass-data-table content-compass-posts-table" });
		const thead = table.createEl("thead").createEl("tr");
		const headersConfig: Array<{ label: string; tooltip?: string }> = [
			{ label: "Chọn" },
			{ label: "Tên bài viết / Câu đầu tiên của bài" },
			{
				label: "Điểm & Tương tác ⓘ",
				tooltip:
					"Công thức tính Điểm tương tác (Score):\n• 1 Like = 1 điểm\n• 1 Bình luận = 2 điểm\n• 1 Chia sẻ = 3 điểm\n────────────────────\nTổng Score = (Likes × 1) + (Comments × 2) + (Shares × 3)",
			},
			{ label: "Lần quét cuối" },
			{
				label: "Đọc & Lưu bài",
				tooltip: "Xem trước toàn văn bài viết/bình luận và lưu thành file Markdown (.md) vào Obsidian Vault",
			},
			{
				label: "Theo dõi",
				tooltip: "Điều khiển tiến trình theo dõi bài viết: Quét cập nhật ngay, Tạm dừng/Tiếp tục tự động quét, hoặc Bỏ theo dõi",
			},
		];
		for (const h of headersConfig) {
			const th = thead.createEl("th", { text: h.label });
			if (h.tooltip) {
				th.setAttribute("title", h.tooltip);
				th.style.cursor = "help";
			}
		}

		const tbody = table.createEl("tbody");

		// Hàm cập nhật tại chỗ (in-place) phần thân bảng tbody mà không vẽ lại toàn trang
		const rebuildTableRows = () => {
			tbody.empty();
			const filteredPosts = getFilteredAndSortedPosts();

			if (filteredPosts.length === 0) {
				const emptyRow = tbody.createEl("tr");
				const emptyTd = emptyRow.createEl("td", {
					cls: "content-compass-placeholder",
					text: "Không có bài viết nào khớp với bộ lọc hiện tại.",
				});
				emptyTd.setAttribute("colspan", "6");
				return;
			}

			for (const { item, st, m, score, authorName, snippet, vaultPath, isSaved, isScraped } of filteredPosts) {
				const fbId = String(st.fb_post_id || item.fb_post_id || "");
				const slugKey = String(st.vault_slug || (fbId ? `fb-post-${fbId}` : ""));
				const row = tbody.createEl("tr", {
					cls: "cc-post-row",
					attr: {
						"data-watch-id": String(item.id || ""),
						"data-fb-id": fbId,
						"data-post-slug": slugKey,
						"data-post-url": String(item.url || ""),
					},
				});

				// 1. Checkbox chon de Luu hoac Xoa hang loat (Apple Rounded Checkbox)
				const chkCell = row.createEl("td");
				const chk = chkCell.createEl("input", {
					type: "checkbox",
					cls: "content-compass-row-checkbox",
				}) as HTMLInputElement;
				chk.checked = this.selectedPostIds.has(item.id);
				chk.addEventListener("change", () => {
					if (chk.checked) {
						this.selectedPostIds.add(item.id);
					} else {
						this.selectedPostIds.delete(item.id);
					}
					syncBulkActionButtons();
				});

			// 2. Hien thi DAM Ten bai hoac Cau dau tien cua bai viet + Source Pill
			const nameCell = row.createEl("td");
			const shortHeadline = snippet.length > 95 ? snippet.slice(0, 92) + "..." : snippet;
			const headlineLink = nameCell.createEl("a", {
				cls: "content-compass-fb-post-headline",
				text: shortHeadline,
				href: item.url,
			});
			headlineLink.setAttribute("target", "_blank");
			headlineLink.setAttribute("rel", "noopener noreferrer");
			headlineLink.setAttribute("title", `Mở trên trình duyệt:\n${snippet}\n${item.url}`);

			// Tính trước dữ liệu Sparkline 5 ngày để nhận diện bài "Mới quét lần đầu"
			const spark5d = this.engagementStore.getPostScoreSparkline5Days(
				[slugKey, fbId, item.id],
				score,
				st.last_polled_at || item.added_at
			);

			const subMeta = nameCell.createDiv({ cls: "content-compass-fb-post-title-row" });
			subMeta.createSpan({
				cls: `content-compass-source-pill ${item.source_type === "own" ? "is-own" : ""}`,
				text: formatSourceTypeLabel(item.source_type),
			});
			const isPostActive = item.enabled !== false;
			subMeta.createSpan({
				cls: `content-compass-source-pill ${isPostActive ? "is-own" : ""}`,
				text: isPostActive
					? "Đang bật quét"
					: item.auto_paused_reason
						? "Đã ngắt (bài cũ)"
						: "Đã tạm dừng",
			});
			if (isScraped && spark5d.isFirstScan) {
				const firstScanBadge = subMeta.createSpan({
					cls: "content-compass-source-pill is-first-scan",
					text: "Mới quét lần đầu",
				});
				firstScanBadge.setAttribute(
					"title",
					"Bài viết mới chỉ có 1 mốc dữ liệu thu thập (chưa có dữ liệu các ngày trước để so sánh tăng trưởng)"
				);
			}
			const originLabel = item.isDiscovered ? `Từ Trang: ${authorName}` : `Chỉ định trực tiếp (${authorName})`;
			const pubDateStr = st.creation_time
				? " • " + new Date(Number(st.creation_time) * 1000).toLocaleDateString("vi-VN")
				: "";
			subMeta.createSpan({
				text: `${originLabel}${pubDateStr}`,
				cls: "content-compass-fb-subtext",
			});

			// 3. Tong diem Score (Highlight Top 5 + Lua mau Top 3 + Sparkline 5 ngay o Dong 1) & 3 Chi so o Dong 2
			const metricCell = row.createEl("td");
			const likes = Number(m.likes || 0);
			const commentsCnt = Number(m.comments || 0);
			const shares = Number(m.shares || 0);
			const rank = scoreRankMap.get(item.id) || 999;
			const isTop5 = rank <= 5;
			const isTop3 = rank <= 3;
			const badgeRankCls = [
				"content-compass-fb-score-badge",
				isTop5 ? "is-top5" : "",
				isTop3 ? `is-top3 is-rank-${rank}` : "",
			]
				.filter(Boolean)
				.join(" ");

			const scoreTopRow = metricCell.createDiv({ cls: "cc-post-score-top-row" });
			const scoreBadge = createMetricChip(scoreTopRow, "flame", `Score ${score}`, badgeRankCls);
			const rankNote = isTop3
				? `🏆 Hạng #${rank} bài tương tác cao nhất (Top 3)\n`
				: isTop5
					? `⭐ Hạng #${rank} bài tương tác cao nhất (Top 5)\n`
					: "";
			scoreBadge.setAttribute(
				"title",
				`${rankNote}Cách tính Điểm tương tác (Score):\n• Likes: ${likes} × 1 = ${likes} điểm\n• Bình luận: ${commentsCnt} × 2 = ${commentsCnt * 2} điểm\n• Chia sẻ: ${shares} × 3 = ${shares * 3} điểm\n────────────────────\nTổng cộng: ${score} điểm`
			);
			scoreBadge.style.cursor = "help";

			renderPostSparkline5D(scoreTopRow, spark5d, isTop5);

			const mRow = metricCell.createDiv({ cls: "content-compass-fb-metrics-row" });
			const chipLike = createMetricChip(mRow, "thumbs-up", String(likes));
			chipLike.setAttribute("title", `Lượt thích / Cảm xúc: ${likes} (×1 điểm)`);
			const chipCmt = createMetricChip(mRow, "message-circle", String(commentsCnt));
			chipCmt.setAttribute("title", `Bình luận: ${commentsCnt} (×2 điểm)`);
			const chipShare = createMetricChip(mRow, "share-2", String(shares));
			chipShare.setAttribute("title", `Lượt chia sẻ: ${shares} (×3 điểm)`);

			// 4. Thoi gian quet cuoi
			const lastT = st.last_polled_at ? new Date(st.last_polled_at).toLocaleTimeString("vi-VN") : "Chờ quét";
			row.createEl("td", { text: lastT });

			// 5. Cột "Đọc & Lưu bài" (Icon-only đồng bộ màu sắc nhẹ nhàng như nút Xem)
			const vaultTd = row.createEl("td");
			const vaultCell = vaultTd.createDiv({ cls: "content-compass-fb-row-actions" });
			if (isScraped) {
				const btnPreview = vaultCell.createEl("button", {
					cls: "content-compass-icon-btn",
				});
				setBtnContent(btnPreview, "eye");
				btnPreview.setAttribute("title", "Đọc toàn văn bài viết, bình luận và chỉnh tiêu đề trước khi lưu");
				btnPreview.addEventListener("click", async () => {
					const curFbId = st.fb_post_id || item.fb_post_id;
					const cacheData = (await this.readPostCache(curFbId)) || {
						fb_post_id: curFbId,
						author_name: authorName,
						post_text: snippet,
						metrics: m,
						comments_tree: [],
					};
					new ScrapedPostModal(
						this.app,
						cacheData,
						item.source_type || "external",
						isSaved,
						async (customTitle, targetSource) => {
							await this.savePostToVault(item, state, customTitle, targetSource);
							await this.engagementStore.initialize();
							this.renderMainView(rootContainer);
						}
					).open();
				});

				if (isSaved && vaultPath) {
					const btnOpen = vaultCell.createEl("button", {
						cls: "content-compass-icon-btn is-saved-vault",
					});
					setBtnContent(btnOpen, "folder-open");
					btnOpen.setAttribute("title", `Đã lưu tại: ${vaultPath}. Bấm để mở file trong Obsidian.`);
					btnOpen.addEventListener("click", () => {
						this.app.workspace.openLinkText(vaultPath, "", false);
					});
				} else {
					const btnSaveOne = vaultCell.createEl("button", {
						cls: "content-compass-icon-btn",
					});
					setBtnContent(btnSaveOne, "download");
					btnSaveOne.setAttribute("title", "Lưu bài này thành file .md trong Obsidian Vault");
					btnSaveOne.addEventListener("click", async () => {
						setBtnContent(btnSaveOne, "loader", undefined, true);
						await this.savePostToVault(item, state);
						await this.engagementStore.initialize();
						this.renderMainView(rootContainer);
					});
				}
			} else {
				vaultCell.createSpan({ text: "Chờ quét", cls: "content-compass-import-status" });
			}

			// 6. Cột "Theo dõi" (Highlight viền xanh blue cho nút đang bật quét tự động)
			const actTd = row.createEl("td");
			const actCell = actTd.createDiv({ cls: "content-compass-fb-row-actions" });
			const btnScan = actCell.createEl("button", { cls: "content-compass-icon-btn" });
			setBtnContent(btnScan, "refresh-cw");
			btnScan.setAttribute("title", "Quét cập nhật chỉ số và bình luận của bài này ngay");
			btnScan.addEventListener("click", () => {
				setBtnContent(btnScan, "loader", undefined, true);
				this.triggerPythonTracker(
					["--force-id", item.id],
					() => this.renderMainView(rootContainer),
					liveStatusEl
				);
			});

			const btnToggle = actCell.createEl("button", {
				cls: `content-compass-icon-btn ${item.enabled !== false ? "is-active-watch" : ""}`,
			});
			setBtnContent(btnToggle, item.enabled !== false ? "pause" : "play");
			btnToggle.setAttribute(
				"title",
				item.enabled !== false
					? "Đang bật theo dõi & quét tự động (Bấm để tạm dừng)"
					: "Đã ngắt / tạm dừng quét (Bấm để tiếp tục tự động quét bài này)"
			);
				btnToggle.addEventListener("click", async () => {
					if (item.isDiscovered) {
						const target = (state.discovered_posts || []).find((d: any) => d.id === item.id);
						if (target) {
							target.enabled = target.enabled === false ? true : false;
							target.auto_paused_reason = null;
							item.enabled = target.enabled;
							item.auto_paused_reason = null;
						}
						await this.saveTrackerState(state);
					} else {
						item.enabled = !item.enabled;
						item.auto_paused_reason = null;
						await this.saveWatchlist(watchlist);
					}
					syncTableHeaderAndFilterCounts();
					rebuildTableRows();
				});

				const btnDel = actCell.createEl("button", { cls: "content-compass-icon-btn is-danger" });
				setBtnContent(btnDel, "trash-2");
				btnDel.setAttribute("title", "Bỏ theo dõi bài viết này (không xóa file .md đã lưu trong Vault)");
				btnDel.addEventListener("click", async () => {
					this.selectedPostIds.delete(item.id);
					if (item.isDiscovered) {
						const fbId = st.fb_post_id || item.fb_post_id;
						if (fbId && !state.ignored_fb_ids.includes(String(fbId))) {
							state.ignored_fb_ids.push(String(fbId));
						}
						state.discovered_posts = (state.discovered_posts || []).filter((d: any) => d.id !== item.id);
						delete state.posts[item.id];
						await this.saveTrackerState(state);
					} else {
						watchlist.posts = watchlist.posts.filter((x) => x.id !== item.id);
						delete state.posts[item.id];
						await this.saveWatchlist(watchlist);
						await this.saveTrackerState(state);
					}
					this.renderMainView(rootContainer);
				});
			}
		};

		// Gắn sự kiện cập nhật tại chỗ (In-place) cho tất cả bộ lọc / sắp xếp / tìm kiếm / chọn hàng loạt
		selectAllBtn.addEventListener("click", () => {
			for (const ep of getFilteredAndSortedPosts()) {
				this.selectedPostIds.add(ep.item.id);
			}
			syncBulkActionButtons();
			rebuildTableRows();
		});

		clearSelBtn.addEventListener("click", () => {
			this.selectedPostIds.clear();
			syncBulkActionButtons();
			rebuildTableRows();
		});

		selSort.addEventListener("change", () => {
			this.postSortBy = selSort.value as any;
			rebuildTableRows();
		});

		selSourceFilter.addEventListener("change", () => {
			this.postSourceFilter = selSourceFilter.value;
			rebuildTableRows();
		});

		selActiveFilter.addEventListener("change", () => {
			this.postActiveFilter = selActiveFilter.value as "all" | "active" | "paused";
			rebuildTableRows();
		});

		selVaultFilter.addEventListener("change", () => {
			this.postVaultFilter = selVaultFilter.value as "all" | "unsaved" | "saved";
			rebuildTableRows();
		});

		inpSearch.addEventListener("input", () => {
			this.postSearchQuery = inpSearch.value;
			rebuildTableRows();
		});

		rebuildTableRows();
	}

	// Nhom 6: Form nhap thu cong (giu nguyen cho cac nen tang khac)
	private renderManualForm(container: HTMLElement): void {
		container.empty();
		const form = container.createDiv({ cls: "content-compass-import-form" });

		const labelPostId = form.createEl("label");
		labelPostId.createSpan({ text: "Post ID (slug bài viết)" });
		const inputPostId = labelPostId.createEl("input", { type: "text", placeholder: "ten-bai-viet-slug" });

		const labelPlatform = form.createEl("label");
		labelPlatform.createSpan({ text: "Platform" });
		const selectPlatform = labelPlatform.createEl("select");
		for (const p of ["facebook", "blog", "youtube", "tiktok", "instagram"]) {
			selectPlatform.createEl("option", { value: p, text: p });
		}

		const labelDate = form.createEl("label");
		labelDate.createSpan({ text: "Ngày thu thập" });
		const inputDate = labelDate.createEl("input", { type: "date" });
		inputDate.value = new Date().toISOString().split("T")[0];

		form.createDiv();

		const labelLikes = form.createEl("label");
		labelLikes.createSpan({ text: "Likes" });
		const inputLikes = labelLikes.createEl("input", { type: "number", placeholder: "0" });
		(inputLikes as HTMLInputElement).value = "0";

		const labelComments = form.createEl("label");
		labelComments.createSpan({ text: "Comments" });
		const inputComments = labelComments.createEl("input", { type: "number", placeholder: "0" });
		(inputComments as HTMLInputElement).value = "0";

		const labelShares = form.createEl("label");
		labelShares.createSpan({ text: "Shares" });
		const inputShares = labelShares.createEl("input", { type: "number", placeholder: "0" });
		(inputShares as HTMLInputElement).value = "0";

		const labelViews = form.createEl("label");
		labelViews.createSpan({ text: "Views" });
		const inputViews = labelViews.createEl("input", { type: "number", placeholder: "0" });
		(inputViews as HTMLInputElement).value = "0";

		const actions = form.createDiv({ cls: "content-compass-import-actions" });
		const saveBtn = actions.createEl("button", { cls: "content-compass-import-btn" });
		setBtnContent(saveBtn, "check", "Lưu engagement");
		const statusMsg = actions.createSpan({ cls: "content-compass-import-status" });

		saveBtn.addEventListener("click", async () => {
			const postId = (inputPostId as HTMLInputElement).value.trim();
			if (!postId) {
				statusMsg.setText("Vui lòng nhập Post ID");
				return;
			}

			const record: EngagementRecord = {
				post_id: postId,
				platform: (selectPlatform as HTMLSelectElement).value,
				collected_at: new Date((inputDate as HTMLInputElement).value + "T00:00:00+07:00").toISOString(),
				metrics: {
					likes: parseInt((inputLikes as HTMLInputElement).value) || 0,
					comments: parseInt((inputComments as HTMLInputElement).value) || 0,
					shares: parseInt((inputShares as HTMLInputElement).value) || 0,
					views: parseInt((inputViews as HTMLInputElement).value) || 0,
				},
			};

			try {
				setBtnContent(saveBtn, "loader", "Đang lưu...", true);
				await this.engagementStore.addRecord(record);
				statusMsg.setText("Đã lưu thành công.");
				statusMsg.style.color = "var(--text-success)";

				(inputPostId as HTMLInputElement).value = "";
				(inputLikes as HTMLInputElement).value = "0";
				(inputComments as HTMLInputElement).value = "0";
				(inputShares as HTMLInputElement).value = "0";
				(inputViews as HTMLInputElement).value = "0";
				if (this.onRefreshDashboard) this.onRefreshDashboard();
			} catch (err) {
				statusMsg.setText("Lỗi khi lưu: " + String(err));
				statusMsg.style.color = "var(--text-error)";
			} finally {
				setBtnContent(saveBtn, "check", "Lưu engagement");
			}
		});
	}

	// Nhom 7: Form import CSV
	private renderCsvForm(container: HTMLElement): void {
		container.empty();
		const wrapper = container.createDiv({ cls: "content-compass-import-form" });

		const desc = wrapper.createDiv({ cls: "content-compass-import-actions" });
		desc.createSpan({
			text: "Format CSV: post_id, platform, collected_at, likes, comments, shares, views",
			cls: "content-compass-fb-subtext",
		});

		const fileLabel = wrapper.createDiv({ cls: "content-compass-import-actions" });
		const fileInput = fileLabel.createEl("input", { type: "file" });
		fileInput.setAttribute("accept", ".csv");

		const importBtn = fileLabel.createEl("button", { cls: "content-compass-import-btn" });
		setBtnContent(importBtn, "upload", "Import CSV");
		importBtn.setAttribute("disabled", "true");

		const statusMsg = wrapper.createDiv({ cls: "content-compass-import-actions" });
		const statusSpan = statusMsg.createSpan({ cls: "content-compass-import-status" });

		let parsedRecords: EngagementRecord[] = [];

		fileInput.addEventListener("change", () => {
			const file = (fileInput as HTMLInputElement).files?.[0];
			if (!file) return;

			const reader = new FileReader();
			reader.onload = (e) => {
				const text = e.target?.result as string;
				parsedRecords = this.parseCsv(text);
				if (parsedRecords.length > 0) {
					statusSpan.setText(`Tìm thấy ${parsedRecords.length} bản ghi hợp lệ. Bấm Import CSV để lưu.`);
					importBtn.removeAttribute("disabled");
				} else {
					statusSpan.setText("Không tìm thấy bản ghi hợp lệ trong file CSV.");
				}
			};
			reader.readAsText(file);
		});

		importBtn.addEventListener("click", async () => {
			if (parsedRecords.length === 0) return;

			try {
				setBtnContent(importBtn, "loader", "Đang import...", true);
				await this.engagementStore.addRecords(parsedRecords);
				statusSpan.setText(`Đã import ${parsedRecords.length} bản ghi thành công.`);
				statusSpan.style.color = "var(--text-success)";
				parsedRecords = [];
				importBtn.setAttribute("disabled", "true");
				if (this.onRefreshDashboard) this.onRefreshDashboard();
			} catch (err) {
				statusSpan.setText("Lỗi: " + String(err));
				statusSpan.style.color = "var(--text-error)";
			} finally {
				setBtnContent(importBtn, "upload", "Import CSV");
			}
		});
	}

	// Nhom 8: Parse CSV thanh mang EngagementRecord
	private parseCsv(text: string): EngagementRecord[] {
		const lines = text.split("\n").map((l) => l.trim()).filter((l) => l.length > 0);
		if (lines.length < 2) return [];

		const records: EngagementRecord[] = [];
		for (let i = 1; i < lines.length; i++) {
			const cols = lines[i].split(",").map((c) => c.trim());
			if (cols.length < 7) continue;

			const [postId, platform, collectedAt, likes, comments, shares, views] = cols;
			if (!postId || !platform) continue;

			let dateStr = collectedAt;
			if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
				dateStr = dateStr + "T00:00:00+07:00";
			}

			records.push({
				post_id: postId,
				platform: platform,
				collected_at: new Date(dateStr).toISOString(),
				metrics: {
					likes: parseInt(likes) || 0,
					comments: parseInt(comments) || 0,
					shares: parseInt(shares) || 0,
					views: parseInt(views) || 0,
				},
			});
		}

		return records;
	}

	// Nhom 9: Hien thi lich su nhap gan day
	private renderRecentHistory(card: HTMLElement): void {
		const recent = this.engagementStore.getRecentRecords(5);
		if (recent.length === 0) return;

		const section = card.createDiv({
			cls: `content-compass-recent-imports ${this.isRecentHistoryCollapsed ? "is-collapsed" : ""}`,
		});
		const header = section.createDiv({ cls: "content-compass-card-header" });
		const subtitle = header.createDiv({ cls: "content-compass-card-subtitle cc-collapsible-title" });
		const bodyWrap = section.createDiv({ cls: "cc-card-collapsible-body" });
		if (this.isRecentHistoryCollapsed) {
			bodyWrap.style.display = "none";
		}
		const syncRecentTitle = () => {
			setBtnContent(
				subtitle,
				this.isRecentHistoryCollapsed ? "chevron-right" : "chevron-down",
				"Lịch sử nhập gần đây:"
			);
			subtitle.setAttribute(
				"title",
				this.isRecentHistoryCollapsed ? "Bấm để Hiện bảng" : "Bấm để Ẩn bảng"
			);
		};
		syncRecentTitle();
		subtitle.addEventListener("click", () => {
			this.isRecentHistoryCollapsed = !this.isRecentHistoryCollapsed;
			section.toggleClass("is-collapsed", this.isRecentHistoryCollapsed);
			bodyWrap.style.display = this.isRecentHistoryCollapsed ? "none" : "";
			syncRecentTitle();
		});

		const table = bodyWrap.createEl("table", { cls: "content-compass-data-table" });
		const thead = table.createEl("thead");
		const headerRow = thead.createEl("tr");
		for (const h of ["Post", "Platform", "Score", "Ngày"]) {
			headerRow.createEl("th", { text: h });
		}

		const tbody = table.createEl("tbody");
		for (const rec of recent) {
			const row = tbody.createEl("tr");
			const postCell = row.createEl("td");
			const shortId = rec.post_id.length > 25 ? rec.post_id.slice(0, 22) + "..." : rec.post_id;
			postCell.setText(shortId);
			postCell.setAttribute("title", rec.post_id);

			row.createEl("td", { text: rec.platform });

			const score = (rec.metrics.likes || 0) + (rec.metrics.comments || 0) * 2 + (rec.metrics.shares || 0) * 3;
			row.createEl("td", { text: String(score) });

			const date = new Date(rec.collected_at);
			row.createEl("td", { text: `${date.getDate()}/${date.getMonth() + 1}` });
		}
	}
}
