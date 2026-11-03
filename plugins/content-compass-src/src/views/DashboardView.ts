/**
 * Tên file: DashboardView.ts
 * Last update: 03/11/2026 15:29 (GMT+7)
 * Vai tro: Obsidian ItemView chinh dong vai tro container cho toan bo giao dien Content Compass.
 * Duoc su dung khi nao?: Khi user mo view qua Ribbon icon hoac Command Palette.
 * Output: Cua so Dashboard da tab (Strategy, Analytics, Advisor) tren workspace leaf cua Obsidian.
 * Tom tat logic hoat dong: Khoi tao khung dieu huong Apple UISegmentedControl voi icon vector Lucide/SF Symbols,
 * mount cac view con (PillarMapView, HierarchyBrowserView, PillarHealthView, ImportEngineView,
 * TimelineChartView, TagRankingView) vao noi dung tab tuong ung.
 */

import { ItemView, WorkspaceLeaf, setIcon } from "obsidian";
import { TagIndex } from "../data/TagIndex";
import { AudienceIndex } from "../data/AudienceIndex";
import { PillarMapView } from "./PillarMapView";
import { HierarchyBrowserView } from "./HierarchyBrowserView";
import { PillarHealthView } from "./PillarHealthView";
import { EngagementStore } from "../data/EngagementStore";
import { ImportEngineView } from "./ImportEngineView";
import { TimelineChartView } from "./TimelineChartView";
import { TagRankingView } from "./TagRankingView";

// Nhóm 1: Hằng số định danh View & hàm tiện ích gắn Icon Vector đơn sắc
export const VIEW_TYPE_CONTENT_COMPASS = "content-compass-dashboard";

function setIconLabel(el: HTMLElement, iconName: string, labelText: string, spinning = false): void {
	el.empty();
	const ic = el.createSpan({ cls: `cc-icon ${spinning ? "is-spinning" : ""}` });
	setIcon(ic, iconName);
	el.createSpan({ text: labelText });
}

// Nhóm 2: Lớp DashboardView mở rộng từ ItemView của Obsidian
export class DashboardView extends ItemView {
	private tagIndex: TagIndex;
	private audienceIndex: AudienceIndex;
	private engagementStore: EngagementStore;
	private activeTab: "strategy" | "analytics" | "advisor" = "strategy";
	private contentArea: HTMLElement | null = null;

	constructor(leaf: WorkspaceLeaf, tagIndex: TagIndex, audienceIndex: AudienceIndex, engagementStore: EngagementStore) {
		super(leaf);
		this.tagIndex = tagIndex;
		this.audienceIndex = audienceIndex;
		this.engagementStore = engagementStore;
	}

	public getViewType(): string {
		return VIEW_TYPE_CONTENT_COMPASS;
	}

	public getDisplayText(): string {
		return "Content Compass";
	}

	public getIcon(): string {
		return "compass";
	}

	// Nhóm 3: Vòng đời nạp giao diện Dashboard
	public async onOpen(): Promise<void> {
		const container = this.containerEl.children[1] as HTMLElement;
		container.empty();
		container.addClass("content-compass-container");

		// Dựng Tab Bar chuẩn Apple UISegmentedControl và nút làm mới
		const tabBar = container.createDiv({ cls: "content-compass-tab-bar" });

		const tabs: Array<{ id: "strategy" | "analytics" | "advisor"; icon: string; label: string }> = [
			{ id: "strategy", icon: "compass", label: "Strategy" },
			{ id: "analytics", icon: "bar-chart-2", label: "Analytics" },
			{ id: "advisor", icon: "sparkles", label: "Advisor" },
		];

		const tabsGroup = tabBar.createDiv({ cls: "content-compass-tabs-group" });

		this.contentArea = container.createDiv({ cls: "content-compass-tab-content" });

		for (const tab of tabs) {
			const btn = tabsGroup.createEl("button", {
				cls: `content-compass-tab-btn ${this.activeTab === tab.id ? "is-active" : ""}`,
			});
			setIconLabel(btn, tab.icon, tab.label);

			btn.addEventListener("click", () => {
				this.activeTab = tab.id;
				tabsGroup.querySelectorAll(".content-compass-tab-btn").forEach((el) => {
					el.removeClass("is-active");
				});
				btn.addClass("is-active");
				if (this.contentArea) {
					this.renderTabContent(this.contentArea);
				}
			});
		}

		// Nút Refresh thủ công với Icon Vector
		const actionsGroup = tabBar.createDiv({ cls: "content-compass-tab-actions" });
		const refreshBtn = actionsGroup.createEl("button", {
			cls: "content-compass-refresh-btn",
		});
		setIconLabel(refreshBtn, "refresh-cw", "Làm mới");
		refreshBtn.setAttribute("title", "Tải lại dữ liệu Audience và Topic từ Vault");
		refreshBtn.addEventListener("click", async () => {
			setIconLabel(refreshBtn, "loader", "Đang tải...", true);
			await this.audienceIndex.initialize();
			await this.tagIndex.initialize();
			await this.engagementStore.initialize();
			this.refresh();
			setIconLabel(refreshBtn, "refresh-cw", "Làm mới");
		});

		// Nạp nội dung tab mặc định
		this.renderTabContent(this.contentArea);
	}

	// Nhóm 4: Phương thức làm mới giao diện tức thời
	public refresh(): void {
		if (this.contentArea) {
			this.renderTabContent(this.contentArea);
		}
	}

	// Nhóm 5: Render nội dung theo Tab đang chọn
	private renderTabContent(contentEl: HTMLElement): void {
		contentEl.empty();

		if (this.activeTab === "strategy") {
			const strategyLayout = contentEl.createDiv({ cls: "content-compass-strategy-layout" });

			// Khối trên: Pillar Treemap
			const topSection = strategyLayout.createDiv({ cls: "content-compass-top-section" });
			const pillarMapView = new PillarMapView(topSection, this.tagIndex, this.audienceIndex, this.app, this.engagementStore);
			pillarMapView.render();

			// Khối dưới: Hierarchy Browser (trái) và Pillar Health (phải)
			const bottomSection = strategyLayout.createDiv({ cls: "content-compass-bottom-section" });

			const hierarchyView = new HierarchyBrowserView(bottomSection, this.audienceIndex, this.app);
			hierarchyView.render();

			const healthView = new PillarHealthView(bottomSection, this.tagIndex, this.audienceIndex);
			healthView.render();
		} else if (this.activeTab === "analytics") {
			const analyticsLayout = contentEl.createDiv({ cls: "content-compass-analytics-layout" });

			// Khoi tren: Import Engine
			const importSection = analyticsLayout.createDiv({ cls: "content-compass-analytics-import" });
			const importView = new ImportEngineView(
				importSection,
				this.engagementStore,
				this.app,
				() => this.refresh()
			);
			importView.render();

			// Khoi giua: Timeline Chart (ket noi callback click bai viet tren chart -> nhay toi bai viet o Bang Danh sach bai viet)
			const timelineSection = analyticsLayout.createDiv({ cls: "content-compass-analytics-chart" });
			const timelineView = new TimelineChartView(
				timelineSection,
				this.engagementStore,
				this.audienceIndex,
				(post) => {
					void importView.focusAndHighlightPost(post);
				}
			);
			timelineView.render();

			// Khoi duoi: Tag Ranking
			const rankingSection = analyticsLayout.createDiv({ cls: "content-compass-analytics-chart" });
			const rankingView = new TagRankingView(rankingSection, this.engagementStore, this.audienceIndex);
			rankingView.render();
		} else if (this.activeTab === "advisor") {
			const placeholder = contentEl.createDiv({ cls: "content-compass-placeholder" });
			setIconLabel(
				placeholder,
				"sparkles",
				"Module Advisor: Sẽ được kích hoạt tại Phase 3 (Đề xuất ý tưởng & chủ đề theo trọng số Buyer Job)."
			);
		}
	}

	public async onClose(): Promise<void> {
		this.contentArea = null;
	}
}
