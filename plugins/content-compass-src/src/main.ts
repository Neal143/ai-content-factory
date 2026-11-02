/**
 * Tên file: main.ts
 * Last update: 29/10/2026 15:55 (GMT+7)
 * Vai tro: Diem nhap (entry point) chinh cua plugin Content Compass trong Obsidian.
 * Duoc su dung khi nao?: Duoc Obsidian goi phuong thuc onload() khi bat plugin hoac khoi dong app.
 * Output: Dang ky View, Ribbon Icon, Command Palette, khoi tao cac Data Index/Store va lang nghe su kien cache + fs.watch.
 * Tom tat logic hoat dong: Khoi tao AudienceIndex, TagIndex, EngagementStore, dang ky DashboardView,
 * gan icon compass vao ribbon, command mo dashboard, tu dong refresh khi file thay doi (audience + engagement)
 * va kich hoat định kỳ Facebook Tracker.
 */

import { Plugin, WorkspaceLeaf } from "obsidian";
import { AudienceIndex } from "./data/AudienceIndex";
import { TagIndex } from "./data/TagIndex";
import { EngagementStore } from "./data/EngagementStore";
import { DashboardView, VIEW_TYPE_CONTENT_COMPASS } from "./views/DashboardView";
import { resolvePythonExe } from "./views/ImportEngineView";

// Nhóm 1: Lớp Plugin chính ContentCompassPlugin
export default class ContentCompassPlugin extends Plugin {
	private audienceIndex: AudienceIndex | null = null;
	private tagIndex: TagIndex | null = null;
	private engagementStore: EngagementStore | null = null;
	private pipelineWatcher: any = null;
	private watcherDebounce: number | null = null;

	// Nhóm 2: Vòng đời khởi chạy Plugin (onload)
	async onload(): Promise<void> {
		console.log("[Content Compass] Khởi chạy plugin...");

		// Khởi tạo các tầng dữ liệu (Data Layer)
		this.audienceIndex = new AudienceIndex(this.app);
		this.tagIndex = new TagIndex(this.app);
		this.engagementStore = new EngagementStore(this.app, this.tagIndex);

		// Dang ky View hien thi Dashboard
		this.registerView(
			VIEW_TYPE_CONTENT_COMPASS,
			(leaf: WorkspaceLeaf) => new DashboardView(leaf, this.tagIndex!, this.audienceIndex!, this.engagementStore!)
		);

		// Thêm icon vào thanh Ribbon bên trái
		this.addRibbonIcon("compass", "Content Compass", () => {
			this.activateView();
		});

		// Thêm Command vào Obsidian Command Palette
		this.addCommand({
			id: "open-content-compass",
			name: "Mở Content Compass Dashboard",
			callback: () => {
				this.activateView();
			},
		});

		// Chờ Obsidian nạp xong cache để khởi tạo Index chính xác
		this.app.workspace.onLayoutReady(async () => {
			if (this.audienceIndex) {
				await this.audienceIndex.initialize();
			}
			if (this.tagIndex) {
				await this.tagIndex.initialize();
			}
			if (this.engagementStore) {
				await this.engagementStore.initialize();
			}
			console.log("[Content Compass] Du lieu AudienceIndex, TagIndex & EngagementStore da san sang.");
			this.refreshOpenViews();
			this.setupPipelineDirectoryWatcher();

			// Kich hoat kiem tra lich quet Facebook Tracker sau khi khoi dong 10 giay
			window.setTimeout(() => this.runDueFacebookTracker(), 10000);
		});

		// Dinh ky moi 5 phut kiem tra va chay cac muc da den han quet trong fb-watchlist.json
		this.registerInterval(
			window.setInterval(() => {
				this.runDueFacebookTracker();
			}, 5 * 60 * 1000)
		);

		// Lắng nghe sự thay đổi file trong vault để cập nhật index và dashboard tức thời
		this.registerEvent(
			this.app.metadataCache.on("changed", async (file) => {
				const normPath = file.path.replace(/\\/g, "/");
				if (normPath.startsWith("01-Atomic/Audiences/")) {
					if (this.audienceIndex) {
						await this.audienceIndex.initialize();
						this.refreshOpenViews();
					}
				} else if (normPath.startsWith("03-Content/")) {
					if (this.engagementStore) {
						await this.engagementStore.initialize();
						this.refreshOpenViews();
					}
				}
			})
		);

		this.registerEvent(
			this.app.vault.on("delete", async (file) => {
				const normPath = file.path.replace(/\\/g, "/");
				if (normPath.startsWith("01-Atomic/Audiences/")) {
					if (this.audienceIndex) {
						await this.audienceIndex.initialize();
						this.refreshOpenViews();
					}
				}
			})
		);
	}

	// Theo doi thu muc an .content-pipeline bang fs.watch (vi Obsidian vault.on bo qua dot-folder)
	private setupPipelineDirectoryWatcher(): void {
		try {
			const fs = require("fs");
			const path = require("path");
			const adapter = this.app.vault.adapter as any;
			const basePath = adapter?.basePath;
			if (!basePath) return;

			const pipelineDir = path.join(basePath, ".content-pipeline");
			if (!fs.existsSync(pipelineDir)) {
				fs.mkdirSync(pipelineDir, { recursive: true });
			}

			this.pipelineWatcher = fs.watch(pipelineDir, { recursive: true }, (_eventType: string, filename: string) => {
				if (!filename) return;
				const norm = filename.replace(/\\/g, "/");
				// Chi lam moi khi file du lieu engagement/*.json thay doi (bo qua file .tmp va .lock)
				if (norm.startsWith("engagement/") && norm.endsWith(".json")) {
					if (this.watcherDebounce) window.clearTimeout(this.watcherDebounce);
					this.watcherDebounce = window.setTimeout(async () => {
						if (this.engagementStore) {
							await this.engagementStore.initialize();
							this.refreshOpenViews();
						}
					}, 600);
				}
			});
		} catch (e) {
			console.warn("[Content Compass] Không thể khởi tạo fs.watch cho .content-pipeline:", e);
		}
	}

	// Kich hoat script Python quet ngam cac bai viet/Fanpage da den han
	private runDueFacebookTracker(): void {
		try {
			const { spawn } = require("child_process");
			const path = require("path");
			const adapter = this.app.vault.adapter as any;
			const vaultPath = adapter?.basePath;
			if (!vaultPath) return;

			const pyExe = resolvePythonExe();
			const scriptPath = path.resolve(vaultPath, "..", ".agents", "scripts", "facebook_realtime_tracker.py");
			spawn(pyExe, [scriptPath, "--vault", vaultPath, "--run-due"], {
				windowsHide: true,
				stdio: "ignore",
			});
		} catch {
			// Bo qua neu moi truong khong ho tro child_process
		}
	}

	// Nhóm 3: Kích hoạt và mở Dashboard Tab trên Workspace
	async activateView(): Promise<void> {
		const { workspace } = this.app;
		let leaf: WorkspaceLeaf | null = null;
		const leaves = workspace.getLeavesOfType(VIEW_TYPE_CONTENT_COMPASS);

		if (leaves.length > 0) {
			leaf = leaves[0];
		} else {
			const rightLeaf = workspace.getLeaf(true);
			if (rightLeaf) {
				leaf = rightLeaf;
				await leaf.setViewState({
					type: VIEW_TYPE_CONTENT_COMPASS,
					active: true,
				});
			}
		}

		if (leaf) {
			workspace.revealLeaf(leaf);
		}
	}

	// Nhóm 4: Cập nhật lại giao diện trên toàn bộ các tab Dashboard đang mở
	private refreshOpenViews(): void {
		const leaves = this.app.workspace.getLeavesOfType(VIEW_TYPE_CONTENT_COMPASS);
		for (const leaf of leaves) {
			if (leaf.view instanceof DashboardView) {
				leaf.view.refresh();
			}
		}
	}

	// Nhóm 5: Dọn dẹp tài nguyên khi tắt Plugin (onunload)
	onunload(): void {
		if (this.watcherDebounce) {
			window.clearTimeout(this.watcherDebounce);
			this.watcherDebounce = null;
		}
		if (this.pipelineWatcher) {
			try {
				this.pipelineWatcher.close();
			} catch {
				// Ignore
			}
			this.pipelineWatcher = null;
		}
		console.log("[Content Compass] Dỡ bỏ plugin thành công.");
	}
}
