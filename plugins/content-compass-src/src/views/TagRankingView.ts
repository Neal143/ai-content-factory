/**
 * Ten file: TagRankingView.ts
 * Last update: 03/11/2026 12:44 (GMT+7)
 * Vai tro: Render Bang Xep hang Hieu suat Da chieu (Theo Tag/Chu de, Top Bai viet, Theo Trang,
 *          Theo Audience, Theo Pillar) ho tro Thanh Phan ra Ty trong (Stacked Bar), Bo loc Multi-select & Nut Hide/Show.
 * Duoc su dung khi nao?: Khi tab Analytics duoc hien thi tren Dashboard.
 * Output: Bo chon 5 chieu phan tich + Che do Stacked Bar (Likes/Comments/Shares) + Multi-select Popover (giu mo khi chon nhieu muc,
 *         cap nhat do thi tuc thoi in-place) + Nut Hide/Show o goc tren cung ben phai + Bieu do thanh ngang HiDPI.
 * Tom tat logic hoat dong: Truy van EngagementStore.queryRankingAdvanced voi bo loc da chon, cap nhat vung Legend/Canvas tai cho (in-place)
 *          ngay khi tich chon trong MultiSelectPopover ma khong dong Popover.
 */

import { setIcon } from "obsidian";
import {
	EngagementStore,
	TagRankEntry,
	RankingDimension,
	ChartMetricType,
	ComponentMetricKey,
	UNASSIGNED_AUDIENCE_KEY,
} from "../data/EngagementStore";
import { AudienceIndex } from "../data/AudienceIndex";
import {
	DateRangeSelection,
	computeRangeForPreset,
	renderDateRangePickerButton,
} from "./DateRangePickerPopover";
import {
	renderMultiSelectPopoverButton,
	MultiSelectOption,
} from "./MultiSelectPopover";

// Nhom 1: Hang so ve bieu do chuan Apple System Colors
const BAR_HEIGHT = 26;
const BAR_GAP = 10;
const CHART_PADDING = { top: 12, right: 185, bottom: 12, left: 275 };
const BAR_COLORS = [
	"#0a84ff", // Apple System Blue
	"#5e5ce6", // Apple System Indigo
	"#30d158", // Apple System Green
	"#ff9f0a", // Apple System Orange
	"#ff375f", // Apple System Pink
];
const STACK_COLORS: Record<ComponentMetricKey, { color: string; label: string; weightLabel: string }> = {
	likes: { color: "#5e5ce6", label: "Likes", weightLabel: "Likes (×1)" },
	comments: { color: "#30d158", label: "Comments", weightLabel: "Comments (×2)" },
	shares: { color: "#ff9f0a", label: "Shares", weightLabel: "Shares (×3)" },
};
const TEXT_COLOR = "hsla(0, 0%, 58%, 0.95)";
const TRACK_COLOR = "hsla(0, 0%, 50%, 0.08)";
const FONT_FAMILY = '-apple-system, BlinkMacSystemFont, "SF Pro Text", "Inter", sans-serif';

// Nhom 2: Lop TagRankingView (Multi-Dimension Performance Ranking)
export class TagRankingView {
	private container: HTMLElement;
	private engagementStore: EngagementStore;
	private audienceIndex: AudienceIndex | null;

	private dimension: RankingDimension = "tag";
	private metric: Exclude<ChartMetricType, "posts"> = "score";
	private selectedComponents: ComponentMetricKey[] = ["likes", "comments", "shares"];
	private barDisplayMode: "stacked" | "single" = "stacked";
	private dateRange: DateRangeSelection = {
		presetId: "90d",
		...computeRangeForPreset("90d"),
		dateBasis: "published",
	};
	private limit: number = 10;
	private selectedSources: string[] = []; // [] = Tat ca nguon
	private selectedAudiences: string[] = []; // [] = Tat ca audience
	private isCollapsed: boolean = false;

	constructor(container: HTMLElement, engagementStore: EngagementStore, audienceIndex?: AudienceIndex) {
		this.container = container;
		this.engagementStore = engagementStore;
		this.audienceIndex = audienceIndex || null;
	}

	// Nhom 3: Render toan bo view voi Bo chon 5 Chieu + Multi-select Filters + Stacked Bar Toggle + In-place Data Section
	public render(): void {
		this.container.empty();

		const card = this.container.createDiv({
			cls: `content-compass-card ${this.isCollapsed ? "is-collapsed" : ""}`,
		});

		// 1. Header: Tieu de (Click de Hide/Show) + Chuyen doi kieu Thanh (Phan ra / Don sac) + Popover Thoi gian
		const header = card.createDiv({ cls: "content-compass-card-header" });
		const title = header.createDiv({ cls: "content-compass-card-title cc-collapsible-title" });
		const titleIcon = title.createSpan({ cls: "cc-icon" });
		title.createSpan({ text: "Bảng Xếp hạng Hiệu suất Đa chiều" });

		const headerControls = header.createDiv({ cls: "content-compass-chart-controls" });
		const cardBody = card.createDiv({ cls: "cc-card-collapsible-body" });
		if (this.isCollapsed) {
			cardBody.style.display = "none";
			headerControls.style.display = "none";
		}

		let renderRankingDataSection = () => {};
		const syncTitleCollapseState = () => {
			titleIcon.empty();
			setIcon(titleIcon, this.isCollapsed ? "chevron-right" : "chevron-down");
			title.setAttribute("title", this.isCollapsed ? "Bấm để Hiện bảng" : "Bấm để Ẩn bảng");
		};
		syncTitleCollapseState();
		title.addEventListener("click", () => {
			this.isCollapsed = !this.isCollapsed;
			card.toggleClass("is-collapsed", this.isCollapsed);
			cardBody.style.display = this.isCollapsed ? "none" : "";
			headerControls.style.display = this.isCollapsed ? "none" : "";
			syncTitleCollapseState();
			if (!this.isCollapsed) {
				renderRankingDataSection();
			}
		});

		if (!this.engagementStore.hasData()) {
			const placeholder = cardBody.createDiv({ cls: "content-compass-placeholder" });
			placeholder.setText("Chưa có dữ liệu engagement. Hãy quét hoặc nhập dữ liệu ở bảng trên.");
			return;
		}

		// Công tắc chuyển đổi kiểu thanh: Phân rã màu (Stacked) <-> Đơn sắc (Single)
		const modeSeg = headerControls.createDiv({ cls: "content-compass-segmented-control cc-yaxis-toggle" });
		const btnStacked = modeSeg.createEl("button", {
			cls: `content-compass-tab-btn ${this.barDisplayMode === "stacked" ? "is-active" : ""}`,
			text: "Thanh phân rã màu",
			attr: {
				type: "button",
				title: "Chia mỗi thanh điểm thành 3 đoạn màu tương ứng tỷ trọng đóng góp của Likes, Comments, Shares",
			},
		});
		const btnSingle = modeSeg.createEl("button", {
			cls: `content-compass-tab-btn ${this.barDisplayMode === "single" ? "is-active" : ""}`,
			text: "Thanh đơn",
			attr: {
				type: "button",
				title: "Vẽ một màu đồng nhất cho mỗi thanh xếp hạng",
			},
		});
		btnStacked.addEventListener("click", () => {
			if (this.barDisplayMode !== "stacked") {
				this.barDisplayMode = "stacked";
				btnStacked.addClass("is-active");
				btnSingle.removeClass("is-active");
				renderRankingDataSection();
			}
		});
		btnSingle.addEventListener("click", () => {
			if (this.barDisplayMode !== "single") {
				this.barDisplayMode = "single";
				btnSingle.addClass("is-active");
				btnStacked.removeClass("is-active");
				renderRankingDataSection();
			}
		});

		renderDateRangePickerButton(
			headerControls,
			this.dateRange,
			{ showGroupBy: false, showDateBasis: true },
			(next) => {
				this.dateRange = next;
				renderRankingDataSection();
			}
		);

		// 2. Dải Bộ lọc Đa chiều (5 Chiều Xếp hạng + Multi-select Chỉ số thành phần + Multi-select Nguồn + Multi-select Audience + Top N)
		const filterStrip = cardBody.createDiv({ cls: "content-compass-chart-filter-strip" });
		const rankingDataContainer = cardBody.createDiv({ cls: "cc-chart-data-section" });

		// 2.1. Segmented Pill: 5 Chiều Xếp hạng
		const dimSeg = filterStrip.createDiv({ cls: "content-compass-segmented-control" });
		const dims: Array<{ id: RankingDimension; label: string }> = [
			{ id: "tag", label: "Theo Tag / Chủ đề" },
			{ id: "post", label: "Top Bài viết" },
			{ id: "author", label: "Theo Trang / Tác giả" },
			{ id: "audience", label: "Theo Audience" },
			{ id: "pillar", label: "Theo Pillar" },
		];
		const dimBtns: HTMLButtonElement[] = [];
		for (const d of dims) {
			const b = dimSeg.createEl("button", {
				cls: `content-compass-tab-btn ${this.dimension === d.id ? "is-active" : ""}`,
				text: d.label,
				attr: { type: "button" },
			});
			dimBtns.push(b);
			b.addEventListener("click", () => {
				if (this.dimension !== d.id) {
					this.dimension = d.id;
					dimBtns.forEach((el) => el.removeClass("is-active"));
					b.addClass("is-active");
					renderRankingDataSection();
				}
			});
		}

		// 2.2. Chọn tiêu chí xếp hạng chính
		const metricSelect = filterStrip.createEl("select");
		const metricOpts: Array<{ val: Exclude<ChartMetricType, "posts">; label: string }> = [
			{ val: "score", label: "Xếp theo: Tổng Điểm (Score)" },
			{ val: "avg_score", label: "Xếp theo: TB Score / bài" },
			{ val: "likes", label: "Xếp theo: Lượt thích (Likes)" },
			{ val: "comments", label: "Xếp theo: Bình luận (Comments)" },
			{ val: "shares", label: "Xếp theo: Lượt chia sẻ (Shares)" },
		];
		for (const m of metricOpts) {
			metricSelect.createEl("option", { value: m.val, text: m.label });
		}
		metricSelect.value = this.metric;
		metricSelect.addEventListener("change", () => {
			this.metric = metricSelect.value as Exclude<ChartMetricType, "posts">;
			renderRankingDataSection();
		});

		// 2.3. Multi-select Chỉ số thành phần (Likes, Comments, Shares) đóng góp vào thanh điểm
		const compOptions: MultiSelectOption[] = (["likes", "comments", "shares"] as ComponentMetricKey[]).map(
			(k) => ({
				value: k,
				label: STACK_COLORS[k].weightLabel,
				color: STACK_COLORS[k].color,
			})
		);
		renderMultiSelectPopoverButton(
			filterStrip,
			{
				prefixLabel: "Thành phần",
				allLabel: "Đủ Likes, Comments, Shares",
				options: compOptions,
				selectedValues: this.selectedComponents,
				allWhenEmpty: false,
				minSelected: 1,
				enableSearch: false,
				widthPx: 240,
			},
			(nextComps) => {
				this.selectedComponents = (nextComps as ComponentMetricKey[]) || ["likes", "comments", "shares"];
				renderRankingDataSection();
			}
		);

		// 2.4. Multi-select Nguồn / Trang (Tự động liên kết tất cả Phân loại nguồn + Nhãn tự tạo + Từng Trang)
		const sourceOptions: MultiSelectOption[] = [
			...this.engagementStore.getSourceTypeFilterOptions(),
		];
		for (const author of this.engagementStore.getKnownAuthors()) {
			sourceOptions.push({
				value: `author:${author}`,
				label: author,
				group: "Từng Trang / Tác giả cụ thể",
				color: "#5e5ce6",
			});
		}
		renderMultiSelectPopoverButton(
			filterStrip,
			{
				prefixLabel: "Nguồn",
				allLabel: "Tất cả trang",
				options: sourceOptions,
				selectedValues: this.selectedSources,
				allWhenEmpty: true,
				enableSearch: true,
				widthPx: 280,
			},
			(nextSources) => {
				this.selectedSources = nextSources;
				renderRankingDataSection();
			}
		);

		// 2.5. Multi-select Audience (Giữ mở Popover và cập nhật biểu đồ tức thời)
		if (this.audienceIndex) {
			const audienceOptions: MultiSelectOption[] = [
				{
					value: UNASSIGNED_AUDIENCE_KEY,
					label: "(Chưa gắn Audience / Ngoài Vault)",
					group: "Trạng thái dữ liệu",
					color: "#8e8e93",
				},
			];
			for (const node of this.audienceIndex.getAllNodes().values()) {
				audienceOptions.push({
					value: node.slug,
					label: node.displayName,
					sublabel: node.level ? `Cấp: ${node.level.toUpperCase()}` : undefined,
					group: "Audience trong Vault",
					color: node.level === "big" ? "#ff453a" : node.level === "little" ? "#30d158" : "#0a84ff",
				});
			}
			renderMultiSelectPopoverButton(
				filterStrip,
				{
					prefixLabel: "Audience",
					allLabel: "Tất cả",
					options: audienceOptions,
					selectedValues: this.selectedAudiences,
					allWhenEmpty: true,
					enableSearch: true,
					widthPx: 300,
				},
				(nextAuds) => {
					this.selectedAudiences = nextAuds;
					renderRankingDataSection();
				}
			);
		}

		// 2.6. Chọn số lượng Top N
		const limitSelect = filterStrip.createEl("select");
		for (const n of [5, 10, 15, 25]) {
			limitSelect.createEl("option", { value: String(n), text: `Hiển thị: Top ${n}` });
		}
		limitSelect.value = String(this.limit);
		limitSelect.addEventListener("change", () => {
			this.limit = parseInt(limitSelect.value) || 10;
			renderRankingDataSection();
		});

		// 3. Hàm cập nhật tại chỗ (In-place) phần Chú giải & Biểu đồ thanh ngang mà không đóng Popover
		renderRankingDataSection = () => {
			if (this.isCollapsed) return;
			rankingDataContainer.empty();

			const data = this.engagementStore.queryRankingAdvanced({
				dimension: this.dimension,
				metric: this.metric,
				days: this.dateRange.presetId === "all" ? 0 : 90,
				startDate: this.dateRange.startDate || undefined,
				endDate: this.dateRange.endDate || undefined,
				dateBasis: this.dateRange.dateBasis || "published",
				limit: this.limit,
				sourceFilter: "all",
				sourceFilters: this.selectedSources,
				filterAudiences: this.selectedAudiences,
				selectedMetrics: this.selectedComponents,
			});

			// 4. Chú giải màu khi bật chế độ Thanh phân rã (Stacked Bar)
			if (this.barDisplayMode === "stacked" && data.length > 0) {
				const legendBar = rankingDataContainer.createDiv({ cls: "cc-chart-legend" });
				for (const compKey of this.selectedComponents) {
					const info = STACK_COLORS[compKey];
					const item = legendBar.createSpan({ cls: "cc-legend-item is-static" });
					const dot = item.createSpan({ cls: "cc-legend-dot" });
					dot.style.backgroundColor = info.color;
					item.createSpan({
						cls: "cc-legend-label",
						text:
							this.metric === "score" || this.metric === "avg_score"
								? info.weightLabel
								: info.label,
					});
				}
			}

			// 5. Canvas vẽ biểu đồ thanh ngang
			const canvasWrap = rankingDataContainer.createDiv({ cls: "content-compass-canvas-wrap" });
			const canvas = canvasWrap.createEl("canvas", { cls: "content-compass-chart-canvas" });

			requestAnimationFrame(() => {
				this.drawChart(canvas, data);
			});
		};

		renderRankingDataSection();
	}

	// Nhom 4: Ve bieu do horizontal bar chart (Ho tro Stacked Bar phan ra mau & Single Bar)
	private drawChart(canvas: HTMLCanvasElement, data: TagRankEntry[]): void {
		const dpr = window.devicePixelRatio || 1;
		const rawParentWidth = canvas.parentElement?.clientWidth || 680;
		const containerWidth = Math.max(rawParentWidth, 340);
		const logicalHeight = Math.max(
			CHART_PADDING.top + CHART_PADDING.bottom + data.length * (BAR_HEIGHT + BAR_GAP),
			80
		);

		canvas.style.width = `${containerWidth}px`;
		canvas.style.height = `${logicalHeight}px`;
		canvas.width = Math.floor(containerWidth * dpr);
		canvas.height = Math.floor(logicalHeight * dpr);

		const ctx = canvas.getContext("2d");
		if (!ctx) return;
		ctx.scale(dpr, dpr);

		ctx.clearRect(0, 0, containerWidth, logicalHeight);

		if (data.length === 0) {
			ctx.fillStyle = TEXT_COLOR;
			ctx.font = `500 13px ${FONT_FAMILY}`;
			ctx.textAlign = "center";
			const emptyMsg =
				this.dimension === "tag" || this.dimension === "audience" || this.dimension === "pillar"
					? "Chưa có bài viết nào được lưu trong Vault và gắn dữ liệu này trong khoảng thời gian đang chọn"
					: "Không có dữ liệu khớp với bộ lọc và khoảng thời gian đang chọn";
			ctx.fillText(emptyMsg, containerWidth / 2, logicalHeight / 2);
			return;
		}

		const leftPad = Math.min(CHART_PADDING.left, Math.floor(containerWidth * 0.38));
		const rightPad = CHART_PADDING.right;
		const plotX = leftPad;
		const plotW = Math.max(containerWidth - leftPad - rightPad, 100);
		const maxVal = Math.max(...data.map((d) => d.value), 1);

		for (let i = 0; i < data.length; i++) {
			const entry = data[i];
			const y = CHART_PADDING.top + i * (BAR_HEIGHT + BAR_GAP);
			const totalBarWidth = Math.max((entry.value / maxVal) * plotW, 8);
			const singleColor = BAR_COLORS[i % BAR_COLORS.length];
			const radius = 7;

			// 1. Rãnh nền mờ kiểu iOS Screen Time
			ctx.fillStyle = TRACK_COLOR;
			ctx.beginPath();
			ctx.roundRect(plotX, y, plotW, BAR_HEIGHT, radius);
			ctx.fill();

			// 2. Vẽ thanh dữ liệu: Stacked Bar (Phân rã tỷ trọng) hoặc Single Bar
			const useScoreWeights = this.metric === "score" || this.metric === "avg_score";
			const segParts: Array<{ key: ComponentMetricKey; contrib: number; color: string }> = [
				{
					key: "likes" as ComponentMetricKey,
					contrib: this.selectedComponents.includes("likes")
						? entry.likes * (useScoreWeights ? 1 : 1)
						: 0,
					color: STACK_COLORS.likes.color,
				},
				{
					key: "comments" as ComponentMetricKey,
					contrib: this.selectedComponents.includes("comments")
						? entry.comments * (useScoreWeights ? 2 : 1)
						: 0,
					color: STACK_COLORS.comments.color,
				},
				{
					key: "shares" as ComponentMetricKey,
					contrib: this.selectedComponents.includes("shares")
						? entry.shares * (useScoreWeights ? 3 : 1)
						: 0,
					color: STACK_COLORS.shares.color,
				},
			].filter((p) => p.contrib > 0);

			const sumContrib = segParts.reduce((acc, p) => acc + p.contrib, 0);

			if (this.barDisplayMode === "stacked" && segParts.length > 1 && sumContrib > 0) {
				ctx.save();
				ctx.beginPath();
				ctx.roundRect(plotX, y, totalBarWidth, BAR_HEIGHT, radius);
				ctx.clip();

				let curX = plotX;
				for (let sIdx = 0; sIdx < segParts.length; sIdx++) {
					const seg = segParts[sIdx];
					const segW =
						sIdx === segParts.length - 1
							? plotX + totalBarWidth - curX
							: (seg.contrib / sumContrib) * totalBarWidth;
					ctx.fillStyle = seg.color;
					ctx.fillRect(curX, y, Math.max(segW, 1), BAR_HEIGHT);
					curX += segW;
				}
				ctx.restore();
			} else {
				const fallbackColor =
					this.barDisplayMode === "stacked" && segParts.length === 1
						? segParts[0].color
						: singleColor;
				ctx.fillStyle = fallbackColor;
				ctx.beginPath();
				ctx.roundRect(plotX, y, totalBarWidth, BAR_HEIGHT, radius);
				ctx.fill();
			}

			// 3. Nhãn hạng mục bên trái
			ctx.fillStyle = TEXT_COLOR;
			ctx.font = `500 12px ${FONT_FAMILY}`;
			ctx.textAlign = "right";
			let rawLabel = entry.sublabel ? `[${entry.sublabel}] ${entry.tag}` : entry.tag;
			if (rawLabel.length > 42) rawLabel = rawLabel.slice(0, 40) + "...";
			ctx.fillText(rawLabel, plotX - 10, y + BAR_HEIGHT / 2 + 4);

			// 4. Điểm số chính + phân rã chi tiết bên phải
			ctx.fillStyle = singleColor;
			ctx.font = `650 12px ${FONT_FAMILY}`;
			ctx.textAlign = "left";
			const mainValStr = this.formatNumber(entry.value);
			ctx.fillText(mainValStr, plotX + totalBarWidth + 8, y + BAR_HEIGHT / 2 + 4);

			const mainValWidth = ctx.measureText(mainValStr).width;
			ctx.fillStyle = TEXT_COLOR;
			ctx.font = `500 11px ${FONT_FAMILY}`;
			const detailStr =
				this.dimension === "post"
					? `(${entry.likes}L · ${entry.comments}C · ${entry.shares}S)`
					: `(${entry.postCount} bài · ${entry.likes}L · ${entry.comments}C · ${entry.shares}S)`;
			ctx.fillText(detailStr, plotX + totalBarWidth + 14 + mainValWidth, y + BAR_HEIGHT / 2 + 4);
		}
	}

	private formatNumber(n: number): string {
		if (n >= 1000) return (n / 1000).toFixed(1) + "k";
		return String(n);
	}
}
