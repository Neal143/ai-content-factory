/**
 * Ten file: ImportEngineView.ts
 * Last update: 30/10/2026 16:30 (GMT+7)
 * Vai tro: Bang dieu khien Theo doi Fanpage, Trang ca nhan & Bai viet (hien thi truc dien) kem Ngan keo Thu thap/Nhap du lieu Engagement (mac dinh an de tiet kiem dien tich).
 * Duoc su dung khi nao?: Khi user mo tab Analytics tren Dashboard.
 * Output:
 *  1. Thanh Header gon nhe + Nut bat/tat ngan keo "➕ Thêm nguồn theo dõi / Nhập dữ liệu".
 *  2. Cum nut "🔑 Đăng nhập FB phụ (Quét trang cá nhân)" / "🟢 FB phụ đã kết nối" (Phuong an B - CDP Chrome cach ly) trong ngan keo cai dat.
 *  3. Bang 1 (Luon hien thi): Danh sach cac Fanpage / Trang ca nhan user da chi dinh theo doi (sua truc tiep so bai/lan, xoa 1-click).
 *  4. Bang 2 (Luon hien thi): Danh sach cac Bai viet dang theo doi (hien thi dam Ten bai / Cau dau tien cua bai viet, loc/sap xep theo Score, Xem truoc & Luu vao Vault `03-Content/Posted` hoac `Viral Posts`, xoa don/hang loat).
 * Tom tat logic hoat dong: Khoa cung cac tham so ky thuat bao ve IP (Adaptive Polling 15p/60p/360p, nghi 8s/bai, toi da 20 bai/phien) o tang he thong; ho tro Dual-Context (Tang 3 Khong Cookie + Tang 2 Co Cookie nick phu); luu bai viet duoc chon thanh file .md chuan trong Vault.
 */

import { App, Modal, TFile, setIcon } from "obsidian";
import { EngagementStore, EngagementRecord } from "../data/EngagementStore";

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

// Nhom 1: Dinh nghia cau truc du lieu Watchlist, State va Bo dem bai viet (Khoa cung cac chi so an toan IP)
export interface FbTrackerSettings {
	poll_new_mins: number;
	poll_mid_mins: number;
	poll_old_mins: number;
	page_scan_mins: number;
	delay_seconds: number;
	max_batch_size: number;
	fetch_comments: boolean;
	expand_replies: boolean;
	background_task_enabled: boolean;
}

export interface FbPostWatchItem {
	id: string;
	url: string;
	fb_post_id?: string;
	source_type: "own" | "external";
	enabled: boolean;
	from_page?: string;
	from_page_name?: string;
	added_at: string;
}

export interface FbPageWatchItem {
	id: string;
	page_identifier: string;
	limit: number;
	source_type: "own" | "external";
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
	fetch_comments: true,
	expand_replies: false,
	background_task_enabled: false,
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

// Modal xem truoc toan van noi dung bai viet, cay binh luan va tuy chinh tieu de truoc khi luu vao Vault
class ScrapedPostModal extends Modal {
	private cacheData: any;
	private defaultSourceType: "own" | "external";
	private isSaved: boolean;
	private onSaveWithCustomOpts: (customTitle: string, targetSource: "own" | "external") => Promise<void>;

	constructor(
		app: App,
		cacheData: any,
		defaultSourceType: "own" | "external",
		isSaved: boolean,
		onSaveWithCustomOpts: (customTitle: string, targetSource: "own" | "external") => Promise<void>
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
		selDest.createEl("option", { value: "external", text: "Lưu vào: 03-Content/Viral Posts (Bài tham khảo)" });
		selDest.createEl("option", { value: "own", text: "Lưu vào: 03-Content/Posted (Bài thương hiệu)" });
		selDest.value = this.defaultSourceType;

		const saveBtn = rowBottom.createEl("button", {
			cls: "content-compass-import-btn",
		});
		setBtnContent(saveBtn, "download", this.isSaved ? "Cập nhật lại vào Vault" : "Lưu bài viết vào Vault");
		saveBtn.addEventListener("click", async () => {
			setBtnContent(saveBtn, "loader", "Đang lưu...", true);
			saveBtn.setAttribute("disabled", "true");
			await this.onSaveWithCustomOpts(
				inpTitle.value.trim() || defaultTitle,
				selDest.value as "own" | "external"
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
	private selectedPostIds: Set<string> = new Set();
	private postVaultFilter: "all" | "unsaved" | "saved" = "all";
	private postSourceFilter: string = "all";
	private postSortBy: "score_desc" | "comments_desc" | "shares_desc" | "recent" = "score_desc";
	private postSearchQuery: string = "";
	private livePollTimer: number | null = null;

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

	// Nhom 4: Doc/Ghi file cau hinh Watchlist, State, Cache va Luu bai viet vao Vault
	private async loadWatchlist(): Promise<FbWatchlistData> {
		try {
			if (await this.app.vault.adapter.exists(WATCHLIST_PATH)) {
				const raw = await this.app.vault.adapter.read(WATCHLIST_PATH);
				const parsed = JSON.parse(raw);
				return {
					settings: {
						...LOCKED_SAFE_SETTINGS,
						expand_replies: Boolean(parsed?.settings?.expand_replies),
						background_task_enabled: Boolean(parsed?.settings?.background_task_enabled),
					},
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
		data.settings = {
			...LOCKED_SAFE_SETTINGS,
			expand_replies: Boolean(data.settings?.expand_replies),
			background_task_enabled: Boolean(data.settings?.background_task_enabled),
		};
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
		overrideSourceType?: "own" | "external"
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

		const allPosts: Array<FbPostWatchItem & { isDiscovered?: boolean }> = [
			...watchlist.posts,
			...(Array.isArray(state?.discovered_posts)
				? state.discovered_posts.map((d: any) => ({ ...d, isDiscovered: true }))
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
		const mainStatusLine = statusLine.createSpan({
			text: `Đang theo dõi: ${watchlist.pages.length} Fanpage & ${allPosts.length} Bài viết • ${progressText} (Cập nhật: ${lastRun})`,
		});

		if (state?.status?.last_error) {
			const errSpan = leftStatus.createDiv({ cls: "content-compass-fb-error" });
			setBtnContent(errSpan, "alert-circle", String(state.status.last_error));
		}

		const btnGroup = statusBar.createDiv({ cls: "content-compass-fb-btn-group" });

		// Nut Bat/Tat Ngan keo Thu thap & Nhap du lieu (Mac dinh AN de tiet kiem dien tich)
		const toggleDrawerBtn = btnGroup.createEl("button", {
			cls: `content-compass-refresh-btn ${this.isInputDrawerOpen ? "is-active" : ""}`,
		});
		setBtnContent(
			toggleDrawerBtn,
			this.isInputDrawerOpen ? "chevron-up" : "plus",
			this.isInputDrawerOpen ? "Thu gọn khung nhập liệu" : "Thêm nguồn / Nhập dữ liệu"
		);
		toggleDrawerBtn.setAttribute(
			"title",
			"Mở hoặc ẩn khung thêm Fanpage, thêm Post URL, nhập thủ công và import CSV"
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

	// Ngan keo Nhap lieu (Mac dinh An, chua 3 tab UISegmentedControl)
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
		setBtnContent(tabFb, "globe", "Thêm Fanpage / Post URL");

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

	// Form them nhanh Fanpage & Post URL ben trong Ngan keo Nhap lieu (Su dung cong tac UISwitch)
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

		// Cột trái: Thêm Fanpage chỉ định
		const pageBox = twoFormsGrid.createDiv({ cls: "content-compass-fb-add-box" });
		const pageSub = pageBox.createDiv({ cls: "content-compass-card-subtitle" });
		setBtnContent(pageSub, "users", "Thêm Fanpage / Trang cá nhân cần theo dõi");

		const lblPages = pageBox.createEl("label", { cls: "content-compass-fb-textarea-label" });
		lblPages.createSpan({ text: "Link Fanpage hoặc Trang cá nhân (mỗi dòng 1 địa chỉ):" });
		const txtPages = lblPages.createEl("textarea", {
			attr: {
				rows: "2",
				placeholder: "https://www.facebook.com/share/1BdsZPSQZa/\nhttps://www.facebook.com/TenFanpage",
			},
		}) as HTMLTextAreaElement;

		const pageControls = pageBox.createDiv({ cls: "content-compass-fb-side-controls" });
		const lblPageSrc = pageControls.createEl("label");
		lblPageSrc.createSpan({ text: "Phân loại:" });
		const selPageSrc = lblPageSrc.createEl("select") as HTMLSelectElement;
		selPageSrc.createEl("option", { value: "external", text: "Đối thủ / Bên ngoài" });
		selPageSrc.createEl("option", { value: "own", text: "Thương hiệu của tôi" });

		const lblLimit = pageControls.createEl("label");
		lblLimit.createSpan({ text: "Số bài mới cần lấy/lần (1 - 20):" });
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
			const sourceType = selPageSrc.value as "own" | "external";
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
		selPostSrc.createEl("option", { value: "external", text: "Bài bên ngoài / Đối thủ (Viral Posts)" });
		selPostSrc.createEl("option", { value: "own", text: "Bài của thương hiệu (Posted)" });

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
			const sourceType = selPostSrc.value as "own" | "external";
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
	}

	// Bang 1 (LUON HIEN THI): The phan vung Fanpage / Trang ca nhan chuan Apple Inset Grouped Card
	private renderWatchedFanpagesTable(
		wrapper: HTMLElement,
		watchlist: FbWatchlistData,
		state: any,
		rootContainer: HTMLElement,
		liveStatusEl: HTMLElement
	): void {
		const sectionCard = wrapper.createDiv({ cls: "content-compass-fb-section-card" });
		const header = sectionCard.createDiv({ cls: "content-compass-fb-section-header" });
		const title = header.createDiv({ cls: "content-compass-card-subtitle" });
		setBtnContent(title, "users", `Nguồn Trang đang theo dõi (${watchlist.pages.length})`);

		if (watchlist.pages.length === 0) {
			const empty = sectionCard.createDiv({ cls: "content-compass-placeholder" });
			empty.setText(
				"Chưa có Fanpage hoặc Trang cá nhân nào. Bấm 'Thêm nguồn / Nhập dữ liệu' ở góc trên để thêm."
			);
			return;
		}

		const scrollBox = sectionCard.createDiv({ cls: "content-compass-table-scroll" });
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
			rowSelSource.createEl("option", { value: "external", text: "Đối thủ" });
			rowSelSource.createEl("option", { value: "own", text: "Thương hiệu" });
			rowSelSource.value = pg.source_type || "external";
			rowSelSource.addEventListener("change", async () => {
				pg.source_type = rowSelSource.value as "own" | "external";
				await this.saveWatchlist(watchlist);
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
				cls: "content-compass-icon-btn",
			});
			setBtnContent(btnToggle, pg.enabled ? "pause" : "play");
			btnToggle.setAttribute("title", pg.enabled ? "Tạm dừng tự động quét nguồn này" : "Tiếp tục tự động quét nguồn này");
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

	// Bang 2 (LUON HIEN THI): The phan vung Bai viet dang theo doi chuan Apple Inset Grouped Card
	private renderWatchedPostsTable(
		wrapper: HTMLElement,
		watchlist: FbWatchlistData,
		state: any,
		allPosts: Array<FbPostWatchItem & { isDiscovered?: boolean }>,
		rootContainer: HTMLElement,
		liveStatusEl: HTMLElement
	): void {
		const sectionCard = wrapper.createDiv({ cls: "content-compass-fb-section-card" });
		const header = sectionCard.createDiv({ cls: "content-compass-fb-section-header" });
		const title = header.createDiv({ cls: "content-compass-card-subtitle" });
		setBtnContent(title, "file-text", `Các Bài viết đang theo dõi (${allPosts.length} bài)`);

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

		const getFilteredAndSortedPosts = () => {
			const list = enrichedPosts.filter((ep) => {
				if (this.postVaultFilter === "saved" && !ep.isSaved) return false;
				if (this.postVaultFilter === "unsaved" && ep.isSaved) return false;

				if (this.postSourceFilter === "own" && ep.item.source_type !== "own") return false;
				if (this.postSourceFilter === "external" && ep.item.source_type !== "external") return false;
				if (this.postSourceFilter === "direct" && ep.item.isDiscovered) return false;
				if (
					this.postSourceFilter.startsWith("page:") &&
					ep.item.from_page !== this.postSourceFilter.slice(5)
				) {
					return false;
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

		// Dai Filter Strip lien mach ben duoi Header (Khong bao gio bi huy/ve lai khi doi filter)
		const filterBar = sectionCard.createDiv({ cls: "content-compass-fb-toolbar-strip" });

		const selSort = filterBar.createEl("select", { cls: "content-compass-fb-inline-select" }) as HTMLSelectElement;
		selSort.createEl("option", { value: "score_desc", text: "Sắp xếp: Điểm tương tác (Cao → Thấp)" });
		selSort.createEl("option", { value: "comments_desc", text: "Sắp xếp: Nhiều bình luận nhất" });
		selSort.createEl("option", { value: "shares_desc", text: "Sắp xếp: Nhiều chia sẻ nhất" });
		selSort.createEl("option", { value: "recent", text: "Sắp xếp: Mới thêm gần nhất" });
		selSort.value = this.postSortBy;

		const selSourceFilter = filterBar.createEl("select", { cls: "content-compass-fb-inline-select" }) as HTMLSelectElement;
		selSourceFilter.createEl("option", { value: "all", text: "Nguồn: Tất cả" });
		selSourceFilter.createEl("option", { value: "direct", text: "Chỉ định trực tiếp bằng URL" });
		selSourceFilter.createEl("option", { value: "own", text: "Chỉ bài Thương hiệu" });
		selSourceFilter.createEl("option", { value: "external", text: "Chỉ bài Đối thủ / Bên ngoài" });
		for (const pg of watchlist.pages) {
			const pName = state?.pages?.[pg.id]?.page_name || pg.page_identifier;
			selSourceFilter.createEl("option", {
				value: `page:${pg.page_identifier}`,
				text: `Từ Trang: ${pName}`,
			});
		}
		selSourceFilter.value = this.postSourceFilter;

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
		const postSec = sectionCard.createDiv({ cls: "content-compass-table-scroll content-compass-posts-scroll" });
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
				const row = tbody.createEl("tr");

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

			const subMeta = nameCell.createDiv({ cls: "content-compass-fb-post-title-row" });
			subMeta.createSpan({
				cls: `content-compass-source-pill ${item.source_type === "own" ? "is-own" : ""}`,
				text: item.source_type === "own" ? "Thương hiệu" : "Đối thủ",
			});
			const originLabel = item.isDiscovered ? `Từ Trang: ${authorName}` : `Chỉ định trực tiếp (${authorName})`;
			const pubDateStr = st.creation_time
				? " • " + new Date(Number(st.creation_time) * 1000).toLocaleDateString("vi-VN")
				: "";
			subMeta.createSpan({
				text: `${originLabel}${pubDateStr}`,
				cls: "content-compass-fb-subtext",
			});

			// 3. Tong diem Score & Chi so tuong tac (Vector Icons + Tabular Numbers + Tooltip giải thích chi tiết)
			const metricCell = row.createEl("td");
			const likes = Number(m.likes || 0);
			const commentsCnt = Number(m.comments || 0);
			const shares = Number(m.shares || 0);
			const scoreBadge = createMetricChip(metricCell, "flame", `Score ${score}`, "content-compass-fb-score-badge");
			scoreBadge.setAttribute(
				"title",
				`Cách tính Điểm tương tác (Score):\n• Likes: ${likes} × 1 = ${likes} điểm\n• Bình luận: ${commentsCnt} × 2 = ${commentsCnt * 2} điểm\n• Chia sẻ: ${shares} × 3 = ${shares * 3} điểm\n────────────────────\nTổng cộng: ${score} điểm`
			);
			scoreBadge.style.cursor = "help";

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

			// 5. Cột "Đọc & Lưu bài" (Gói trong div con để không phá vỡ table-cell của <td>)
			const vaultTd = row.createEl("td");
			const vaultCell = vaultTd.createDiv({ cls: "content-compass-fb-row-actions" });
			if (isScraped) {
				const btnPreview = vaultCell.createEl("button", {
					cls: "content-compass-icon-btn",
				});
				setBtnContent(btnPreview, "eye");
				btnPreview.setAttribute("title", "Đọc toàn văn bài viết, bình luận và chỉnh tiêu đề trước khi lưu");
				btnPreview.addEventListener("click", async () => {
					const fbId = st.fb_post_id || item.fb_post_id;
					const cacheData = (await this.readPostCache(fbId)) || {
						fb_post_id: fbId,
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
						cls: "content-compass-refresh-btn",
					});
					setBtnContent(btnOpen, "folder-open", "Mở file");
					btnOpen.setAttribute("title", `Đã lưu tại: ${vaultPath}. Bấm để mở trong Obsidian.`);
					btnOpen.addEventListener("click", () => {
						this.app.workspace.openLinkText(vaultPath, "", false);
					});
				} else {
					const btnSaveOne = vaultCell.createEl("button", {
						cls: "content-compass-import-btn",
					});
					setBtnContent(btnSaveOne, "download", "Lưu");
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

			// 6. Cột "Theo dõi" (Gói trong div con để hiển thị đúng ở cột 6, không bị gộp vào cột 5)
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
				cls: "content-compass-icon-btn",
			});
			setBtnContent(btnToggle, item.enabled !== false ? "pause" : "play");
			btnToggle.setAttribute(
				"title",
				item.enabled !== false ? "Tạm dừng tự động quét bài này" : "Tiếp tục tự động quét bài này"
			);
				btnToggle.addEventListener("click", async () => {
					if (item.isDiscovered) {
						const target = (state.discovered_posts || []).find((d: any) => d.id === item.id);
						if (target) {
							target.enabled = target.enabled === false ? true : false;
							item.enabled = target.enabled;
						}
						await this.saveTrackerState(state);
					} else {
						item.enabled = !item.enabled;
						await this.saveWatchlist(watchlist);
					}
					setBtnContent(btnToggle, item.enabled !== false ? "pause" : "play");
					btnToggle.setAttribute(
						"title",
						item.enabled !== false ? "Tạm dừng tự động quét bài này" : "Tiếp tục tự động quét bài này"
					);
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

		const section = card.createDiv({ cls: "content-compass-recent-imports" });
		const subtitle = section.createDiv({ cls: "content-compass-card-subtitle" });
		subtitle.setText("Lịch sử nhập gần đây:");
		subtitle.style.marginBottom = "4px";

		const table = section.createEl("table", { cls: "content-compass-data-table" });
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
