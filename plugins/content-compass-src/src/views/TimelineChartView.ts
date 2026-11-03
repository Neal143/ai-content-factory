/**
 * Ten file: TimelineChartView.ts
 * Last update: 03/11/2026 15:52 (GMT+7)
 * Vai tro: Render bang phan tich xu huong Engagement Da tuyen (Multi-Series Line Chart + Multi-Select Popover Filters + Nut Thu gon/Mo rong).
 * Duoc su dung khi nao?: Khi tab Analytics duoc hien thi tren Dashboard.
 * Output:
 *   - Chieu tach duong (BreakdownBy: Theo Chi so | Theo Nguon/Trang | Theo Audience) dang Dropdown Single-Choice.
 *   - Bo loc Multi-select Popover cho Chi so, Nguon/Trang, Audience (giu nguyen Popover mo khi chon nhieu muc, cap nhat do thi tuc thoi in-place).
 *   - Nut chuyen doi Truc Y: Gia tri thuc (123) <-> Ty le chuan hoa % (0-100%) + Tieu de click de Hide/Show.
 *   - 4 the KPI tuong tac + Thanh Chu giai (Legend) + HiDPI Canvas kem Pinned Tooltip & Popup Danh sach Bai viet theo moc thoi gian.
 * Tom tat logic hoat dong: Truy van EngagementStore.queryTimelineMultiSeries, ho tro click ghim moc thoi gian tren bieu do,
 *          click vao so bai viet de mo popup danh sach bai viet cua dung duong/nguon do va nhay den bai viet trong bang Danh sach bai viet.
 */

import { setIcon } from "obsidian";
import {
	EngagementStore,
	TimelineSeries,
	ChartMetricType,
	TimelineBreakdownBy,
	TimelinePeriodPostItem,
	formatSourceTypeLabel,
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

// Nhom 1: Hang so ve bieu do chuan Apple Stocks / Health
const CHART_HEIGHT = 265;
const CHART_PADDING = { top: 28, right: 38, bottom: 40, left: 58 };
const GRID_COLOR = "hsla(0, 0%, 50%, 0.14)";
const TEXT_COLOR = "hsla(0, 0%, 58%, 0.95)";
const FONT_FAMILY = '-apple-system, BlinkMacSystemFont, "SF Pro Text", "Inter", sans-serif';

const METRIC_THEMES: Record<ChartMetricType, { line: string; label: string }> = {
	score: { line: "#0a84ff", label: "Tổng Điểm (Score)" },
	avg_score: { line: "#64d2ff", label: "TB Score / bài" },
	likes: { line: "#5e5ce6", label: "Lượt thích (Likes)" },
	comments: { line: "#30d158", label: "Bình luận (Comments)" },
	shares: { line: "#ff9f0a", label: "Chia sẻ (Shares)" },
	posts: { line: "#ff375f", label: "Số lượng bài viết" },
};

// Nhom 2: Lop TimelineChartView
export class TimelineChartView {
	private container: HTMLElement;
	private engagementStore: EngagementStore;
	private audienceIndex: AudienceIndex;
	private onSelectPost?: (post: TimelinePeriodPostItem) => void;
	private outsideClickCleanup: (() => void) | null = null;

	private dateRange: DateRangeSelection = {
		presetId: "90d",
		...computeRangeForPreset("90d"),
		groupBy: "day",
		dateBasis: "published",
	};

	private breakdownBy: TimelineBreakdownBy = "metric";
	private selectedMetrics: ChartMetricType[] = ["score"];
	private selectedSources: string[] = []; // [] = Tat ca nguon
	private selectedAudiences: string[] = []; // [] = Tat ca audience
	private yAxisMode: "raw" | "normalized" = "raw";
	private hiddenSeriesKeys: Set<string> = new Set();
	private isCollapsed: boolean = false;

	constructor(
		container: HTMLElement,
		engagementStore: EngagementStore,
		audienceIndex: AudienceIndex,
		onSelectPost?: (post: TimelinePeriodPostItem) => void
	) {
		this.container = container;
		this.engagementStore = engagementStore;
		this.audienceIndex = audienceIndex;
		this.onSelectPost = onSelectPost;
	}

	// Nhom 3: Render toan bo view voi Header + Multi-Select Filter Strip + In-place Data Section (KPI + Legend + Canvas)
	public render(): void {
		this.container.empty();

		const card = this.container.createDiv({
			cls: `content-compass-card ${this.isCollapsed ? "is-collapsed" : ""}`,
		});

		// 1. Header: Tieu de (Click de Hide/Show) + Chuyen doi Truc Y (123 / %) + Popover Thoi gian
		const header = card.createDiv({ cls: "content-compass-card-header" });
		const title = header.createDiv({ cls: "content-compass-card-title cc-collapsible-title" });
		const titleIcon = title.createSpan({ cls: "cc-icon" });
		title.createSpan({ text: "Xu hướng Engagement theo thời gian" });

		const headerControls = header.createDiv({ cls: "content-compass-chart-controls" });
		const cardBody = card.createDiv({ cls: "cc-card-collapsible-body" });
		if (this.isCollapsed) {
			cardBody.style.display = "none";
			headerControls.style.display = "none";
		}

		let renderChartDataSection = () => {};
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
				renderChartDataSection();
			}
		});

		if (!this.engagementStore.hasData()) {
			const placeholder = cardBody.createDiv({ cls: "content-compass-placeholder" });
			placeholder.setText("Chưa có dữ liệu engagement. Hãy quét hoặc nhập dữ liệu ở bảng trên.");
			return;
		}

		// Công tắc chuyển đổi chế độ trục Y: Giá trị thực (123) <-> Chuẩn hóa % (0-100%)
		const yModeSeg = headerControls.createDiv({ cls: "content-compass-segmented-control cc-yaxis-toggle" });
		const btnRaw = yModeSeg.createEl("button", {
			cls: `content-compass-tab-btn ${this.yAxisMode === "raw" ? "is-active" : ""}`,
			text: "Giá trị thực (123)",
			attr: {
				type: "button",
				title: "Hiển thị trục tung theo con số thực tế",
			},
		});
		const btnNorm = yModeSeg.createEl("button", {
			cls: `content-compass-tab-btn ${this.yAxisMode === "normalized" ? "is-active" : ""}`,
			text: "Chuẩn hóa %",
			attr: {
				type: "button",
				title: "Chuẩn hóa mỗi đường về thang 0–100% theo đỉnh của chính đường đó (giúp so sánh các chỉ số lệch đơn vị như Score và Số bài viết)",
			},
		});
		btnRaw.addEventListener("click", () => {
			if (this.yAxisMode !== "raw") {
				this.yAxisMode = "raw";
				btnRaw.addClass("is-active");
				btnNorm.removeClass("is-active");
				renderChartDataSection();
			}
		});
		btnNorm.addEventListener("click", () => {
			if (this.yAxisMode !== "normalized") {
				this.yAxisMode = "normalized";
				btnNorm.addClass("is-active");
				btnRaw.removeClass("is-active");
				renderChartDataSection();
			}
		});

		renderDateRangePickerButton(
			headerControls,
			this.dateRange,
			{ showGroupBy: true, showDateBasis: true },
			(next) => {
				this.dateRange = next;
				renderChartDataSection();
			}
		);

		// 2. Dải Bộ lọc Đa chiều & Chọn Chiều tách đường (BreakdownBy + Multi-select Popovers)
		const filterStrip = cardBody.createDiv({ cls: "content-compass-chart-filter-strip" });
		const chartDataContainer = cardBody.createDiv({ cls: "cc-chart-data-section" });

		// 2.1. Chọn Chiều tách đường dạng Dropdown Single-Choice gọn trên 1 dòng (Chỉ số | Nguồn / Trang | Audience)
		const breakdownSelect = filterStrip.createEl("select");
		breakdownSelect.setAttribute(
			"title",
			"Chọn đối tượng phân tách thành các đường màu trên biểu đồ (Chỉ số / Nguồn / Audience)"
		);
		const breakdownOpts: Array<{ id: TimelineBreakdownBy; label: string }> = [
			{ id: "metric", label: "Vẽ theo: Chỉ số" },
			{ id: "source", label: "Vẽ theo: Nguồn / Trang" },
			{ id: "audience", label: "Vẽ theo: Audience" },
		];
		for (const b of breakdownOpts) {
			breakdownSelect.createEl("option", {
				value: b.id,
				text: b.label,
			});
		}
		breakdownSelect.value = this.breakdownBy;
		breakdownSelect.addEventListener("change", () => {
			const nextBreakdown = breakdownSelect.value as TimelineBreakdownBy;
			if (this.breakdownBy !== nextBreakdown) {
				this.breakdownBy = nextBreakdown;
				this.hiddenSeriesKeys.clear();
				this.render();
			}
		});

		// 2.2. Bộ chọn Chỉ số (Multi-select khi tách theo Chỉ số; Single-select khi tách theo Nguồn/Audience)
		const metricOptions: MultiSelectOption[] = (Object.keys(METRIC_THEMES) as ChartMetricType[]).map((k) => ({
			value: k,
			label: METRIC_THEMES[k].label,
			color: METRIC_THEMES[k].line,
		}));

		let metricPopoverEl: HTMLElement | null = null;
		let singleMetricSelect: HTMLSelectElement | null = null;

		if (this.breakdownBy === "metric") {
			metricPopoverEl = renderMultiSelectPopoverButton(
				filterStrip,
				{
					prefixLabel: "Chỉ số (Đường)",
					options: metricOptions,
					selectedValues: this.selectedMetrics,
					allWhenEmpty: false,
					minSelected: 1,
					enableSearch: false,
					widthPx: 250,
				},
				(nextVals) => {
					this.selectedMetrics = (nextVals as ChartMetricType[]) || ["score"];
					renderChartDataSection();
				}
			);
		} else {
			const primaryMetric = this.selectedMetrics[0] || "score";
			singleMetricSelect = filterStrip.createEl("select");
			singleMetricSelect.setAttribute("title", "Chọn đơn vị đo trên trục Y cho các đường Nguồn / Audience");
			for (const m of metricOptions) {
				singleMetricSelect.createEl("option", { value: m.value, text: `Đo theo: ${m.label}` });
			}
			singleMetricSelect.value = primaryMetric;
			singleMetricSelect.addEventListener("change", () => {
				if (singleMetricSelect) {
					this.selectedMetrics = [singleMetricSelect.value as ChartMetricType];
					renderChartDataSection();
				}
			});
		}

		// 2.3. Bộ chọn Multi-select Nguồn / Trang (Tự động liên kết tất cả Phân loại nguồn + Nhãn tự tạo + Từng Trang)
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
				prefixLabel: this.breakdownBy === "source" ? "Nguồn (Đường)" : "Lọc Nguồn",
				allLabel: "Tất cả trang",
				options: sourceOptions,
				selectedValues: this.selectedSources,
				allWhenEmpty: true,
				enableSearch: true,
				widthPx: 290,
			},
			(nextSources) => {
				this.selectedSources = nextSources;
				renderChartDataSection();
			}
		);

		// 2.4. Bộ chọn Multi-select Audience (Giữ mở Popover và cập nhật biểu đồ tức thời)
		const audienceLabelMap = new Map<string, string>();
		const audienceOptions: MultiSelectOption[] = [
			{
				value: UNASSIGNED_AUDIENCE_KEY,
				label: "(Chưa gắn Audience / Ngoài Vault)",
				group: "Trạng thái dữ liệu",
				color: "#8e8e93",
			},
		];
		for (const node of this.audienceIndex.getAllNodes().values()) {
			audienceLabelMap.set(node.slug, node.displayName);
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
				prefixLabel: this.breakdownBy === "audience" ? "Audience (Đường)" : "Lọc Audience",
				allLabel: "Tất cả Audience",
				options: audienceOptions,
				selectedValues: this.selectedAudiences,
				allWhenEmpty: true,
				enableSearch: true,
				widthPx: 320,
			},
			(nextAuds) => {
				this.selectedAudiences = nextAuds;
				renderChartDataSection();
			}
		);

		// 3. Hàm cập nhật tại chỗ (In-place) phần KPI + Legend + Canvas mà không đóng Popover đang mở
		renderChartDataSection = () => {
			if (this.isCollapsed) return;
			chartDataContainer.empty();

			const { periods, series, summary } = this.engagementStore.queryTimelineMultiSeries({
				groupBy: this.dateRange.groupBy || "day",
				days: this.dateRange.presetId === "all" ? 0 : 90,
				startDate: this.dateRange.startDate || undefined,
				endDate: this.dateRange.endDate || undefined,
				dateBasis: this.dateRange.dateBasis || "published",
				breakdownBy: this.breakdownBy,
				metrics: this.selectedMetrics,
				sourceFilters: this.selectedSources,
				filterAudiences: this.selectedAudiences,
				audienceLabelMap,
			});

			// 4. Dựng 4 Thẻ KPI Tóm tắt chuẩn Apple Health
			const kpiGrid = chartDataContainer.createDiv({ cls: "content-compass-kpi-grid" });
			const kpiItems: Array<{
				key: ChartMetricType;
				title: string;
				value: string;
				sub: string;
				color: string;
				icon: string;
			}> = [
				{
					key: "score",
					title: "Tổng Điểm (Score)",
					value: summary.totalScore.toLocaleString("vi-VN"),
					sub: `Trung bình: ${summary.avgScorePerPost.toLocaleString("vi-VN")} điểm / bài`,
					color: "#0a84ff",
					icon: "flame",
				},
				{
					key: "likes",
					title: "Tổng Lượt thích",
					value: summary.totalLikes.toLocaleString("vi-VN"),
					sub: "Trọng số: ×1 điểm / like",
					color: "#5e5ce6",
					icon: "thumbs-up",
				},
				{
					key: "comments",
					title: "Tổng Bình luận",
					value: summary.totalComments.toLocaleString("vi-VN"),
					sub: "Trọng số: ×2 điểm / bình luận",
					color: "#30d158",
					icon: "message-circle",
				},
				{
					key: "shares",
					title: "Tổng Chia sẻ",
					value: summary.totalShares.toLocaleString("vi-VN"),
					sub: `Trên tổng số ${summary.postCount} bài viết`,
					color: "#ff9f0a",
					icon: "share-2",
				},
			];

			for (const item of kpiItems) {
				const isSelected =
					this.breakdownBy === "metric"
						? this.selectedMetrics.includes(item.key)
						: this.selectedMetrics[0] === item.key;

				const tile = kpiGrid.createDiv({
					cls: `content-compass-kpi-tile ${isSelected ? "is-selected" : ""}`,
				});
				if (isSelected) {
					tile.style.borderColor = item.color;
				}
				tile.setAttribute(
					"title",
					this.breakdownBy === "metric"
						? `Bấm để Bật / Tắt đường biểu diễn "${item.title}" trên biểu đồ (chọn nhiều thẻ cùng lúc)`
						: `Bấm để chọn "${item.title}" làm chỉ số đo cho các đường`
				);

				const topRow = tile.createDiv({ cls: "content-compass-kpi-title" });
				const ic = topRow.createSpan({ cls: "cc-icon" });
				ic.style.color = item.color;
				setIcon(ic, item.icon);
				topRow.createSpan({ text: item.title });

				const valEl = tile.createDiv({ cls: "content-compass-kpi-value", text: item.value });
				valEl.style.color = item.color;

				tile.createDiv({ cls: "content-compass-kpi-sub", text: item.sub });
				tile.addEventListener("click", () => {
					if (this.breakdownBy === "metric") {
						if (this.selectedMetrics.includes(item.key)) {
							if (this.selectedMetrics.length > 1) {
								this.selectedMetrics = this.selectedMetrics.filter((m) => m !== item.key);
							}
						} else {
							this.selectedMetrics = [...this.selectedMetrics, item.key];
						}
						if (metricPopoverEl && (metricPopoverEl as any).syncSelectedValues) {
							(metricPopoverEl as any).syncSelectedValues(this.selectedMetrics);
						}
					} else {
						this.selectedMetrics = [item.key];
						if (singleMetricSelect) {
							singleMetricSelect.value = item.key;
						}
					}
					renderChartDataSection();
				});
			}

			// 5. Thanh Chú giải Tương tác (Interactive Series Legend)
			if (series.length > 0 && periods.length > 0) {
				const legendBar = chartDataContainer.createDiv({ cls: "cc-chart-legend" });
				for (const s of series) {
					const isHidden = this.hiddenSeriesKeys.has(s.key);
					const chip = legendBar.createEl("button", {
						cls: `cc-legend-item ${isHidden ? "is-muted" : ""}`,
						attr: {
							type: "button",
							title: "Bấm để ẩn / hiện đường này trên đồ thị",
						},
					});
					const dot = chip.createSpan({ cls: "cc-legend-dot" });
					dot.style.backgroundColor = s.color;
					chip.createSpan({ cls: "cc-legend-label", text: s.label });
					chip.createSpan({
						cls: "cc-legend-val",
						text: s.totalValue.toLocaleString("vi-VN"),
					});
					chip.addEventListener("click", () => {
						if (this.hiddenSeriesKeys.has(s.key)) {
							this.hiddenSeriesKeys.delete(s.key);
						} else {
							const visibleCount = series.filter((x) => !this.hiddenSeriesKeys.has(x.key)).length;
							if (visibleCount > 1) {
								this.hiddenSeriesKeys.add(s.key);
							}
						}
						renderChartDataSection();
					});
				}
			}

			// 6. Khung Canvas vẽ biểu đồ Đa tuyến + Floating/Pinned Tooltip + Popup Danh sách Bài viết
			const canvasWrap = chartDataContainer.createDiv({ cls: "content-compass-canvas-wrap cc-canvas-interactive-wrap" });
			const canvas = canvasWrap.createEl("canvas", { cls: "content-compass-chart-canvas" });
			canvas.height = CHART_HEIGHT;
			const tooltipEl = canvasWrap.createDiv({ cls: "cc-chart-tooltip is-hidden" });
			const postsPopupEl = canvasWrap.createDiv({ cls: "cc-chart-posts-popover is-hidden" });

			const visibleSeries = series.filter((s) => !this.hiddenSeriesKeys.has(s.key));

			requestAnimationFrame(() => {
				this.drawMultiSeriesChart(canvas, tooltipEl, postsPopupEl, periods, visibleSeries);
			});
		};

		renderChartDataSection();
	}

	// Nhom 4: Ve bieu do Multi-Series Line Chart len Canvas kem Hover Crosshair, Click-to-Pin Tooltip & Post Drilldown Popup
	private drawMultiSeriesChart(
		canvas: HTMLCanvasElement,
		tooltipEl: HTMLElement,
		postsPopupEl: HTMLElement,
		periods: string[],
		seriesList: TimelineSeries[]
	): void {
		if (this.outsideClickCleanup) {
			this.outsideClickCleanup();
			this.outsideClickCleanup = null;
		}
		const dpr = window.devicePixelRatio || 1;
		const rawParentWidth = canvas.parentElement?.clientWidth || 680;
		const containerWidth = Math.max(rawParentWidth, 320);

		canvas.style.width = `${containerWidth}px`;
		canvas.style.height = `${CHART_HEIGHT}px`;
		canvas.width = Math.floor(containerWidth * dpr);
		canvas.height = Math.floor(CHART_HEIGHT * dpr);

		const ctx = canvas.getContext("2d");
		if (!ctx) return;

		const renderScene = (hoverIndex: number | null) => {
			ctx.save();
			ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
			ctx.clearRect(0, 0, containerWidth, CHART_HEIGHT);

			if (periods.length === 0 || seriesList.length === 0) {
				ctx.fillStyle = TEXT_COLOR;
				ctx.font = `500 13px ${FONT_FAMILY}`;
				ctx.textAlign = "center";
				ctx.fillText(
					"Không có dữ liệu khớp với bộ lọc đang chọn",
					containerWidth / 2,
					CHART_HEIGHT / 2
				);
				ctx.restore();
				return;
			}

			const plotX = CHART_PADDING.left;
			const plotY = CHART_PADDING.top;
			const plotW = containerWidth - CHART_PADDING.left - CHART_PADDING.right;
			const plotH = CHART_HEIGHT - CHART_PADDING.top - CHART_PADDING.bottom;

			const isNormalized = this.yAxisMode === "normalized";
			const globalMaxVal = Math.max(
				...seriesList.flatMap((s) => s.points.map((p) => p.value)),
				1
			);

			// 1. Vẽ đường lưới ngang nét đứt chuẩn Apple Health
			ctx.strokeStyle = GRID_COLOR;
			ctx.lineWidth = 1;
			ctx.setLineDash([4, 4]);
			for (let i = 0; i <= 4; i++) {
				const y = plotY + plotH - (plotH / 4) * i;
				ctx.beginPath();
				ctx.moveTo(plotX, y);
				ctx.lineTo(plotX + plotW, y);
				ctx.stroke();

				ctx.fillStyle = TEXT_COLOR;
				ctx.font = `500 11px ${FONT_FAMILY}`;
				ctx.textAlign = "right";
				if (isNormalized) {
					ctx.fillText(`${i * 25}%`, plotX - 10, y + 4);
				} else {
					const val = Math.round((globalMaxVal / 4) * i);
					ctx.fillText(val.toLocaleString("vi-VN"), plotX - 10, y + 4);
				}
			}
			ctx.setLineDash([]);

			const xStep = periods.length > 1 ? plotW / (periods.length - 1) : plotW / 2;
			const getX = (idx: number) => (periods.length === 1 ? plotX + plotW / 2 : plotX + xStep * idx);

			// 2. Vẽ đường gióng dọc (Crosshair) nếu đang di chuột
			if (hoverIndex !== null && hoverIndex >= 0 && hoverIndex < periods.length) {
				const hx = getX(hoverIndex);
				ctx.strokeStyle = "hsla(0, 0%, 55%, 0.45)";
				ctx.lineWidth = 1;
				ctx.setLineDash([3, 3]);
				ctx.beginPath();
				ctx.moveTo(hx, plotY);
				ctx.lineTo(hx, plotY + plotH);
				ctx.stroke();
				ctx.setLineDash([]);
			}

			// 3. Vẽ từng đường biểu diễn (Series)
			const isSingleSeries = seriesList.length === 1;
			const showEveryVal = Math.max(1, Math.ceil(periods.length / 12));

			for (const series of seriesList) {
				const seriesMax = Math.max(...series.points.map((p) => p.value), 1);
				const pts = series.points.map((d, idx) => {
					const ratio = isNormalized ? d.value / seriesMax : d.value / globalMaxVal;
					return {
						x: getX(idx),
						y: plotY + plotH - ratio * plotH,
						rawValue: d.value,
						pctValue: Math.round((d.value / seriesMax) * 100),
						period: d.period,
						postCount: d.recordCount,
					};
				});

				// Tô vùng Area Gradient bên dưới (Đậm khi 1 đường, Rất nhẹ khi nhiều đường để không đục màu)
				if (pts.length > 1) {
					const areaGrad = ctx.createLinearGradient(0, plotY, 0, plotY + plotH);
					areaGrad.addColorStop(0, this.hexToRgba(series.color, isSingleSeries ? 0.25 : 0.06));
					areaGrad.addColorStop(1, this.hexToRgba(series.color, 0.0));
					ctx.fillStyle = areaGrad;
					ctx.beginPath();
					ctx.moveTo(pts[0].x, plotY + plotH);
					for (const p of pts) ctx.lineTo(p.x, p.y);
					ctx.lineTo(pts[pts.length - 1].x, plotY + plotH);
					ctx.closePath();
					ctx.fill();
				}

				// Vẽ đường chính sắc nét
				ctx.strokeStyle = series.color;
				ctx.lineWidth = isSingleSeries ? 2.6 : 2.2;
				ctx.lineJoin = "round";
				ctx.lineCap = "round";
				ctx.beginPath();
				for (let i = 0; i < pts.length; i++) {
					if (i === 0) ctx.moveTo(pts[i].x, pts[i].y);
					else ctx.lineTo(pts[i].x, pts[i].y);
				}
				ctx.stroke();

				// Vẽ nút điểm dữ liệu (Data Points)
				for (let i = 0; i < pts.length; i++) {
					const p = pts[i];
					const isHovered = hoverIndex === i;
					const outerR = isHovered ? 5.5 : 4.2;
					const innerR = isHovered ? 3.8 : 2.9;

					ctx.fillStyle = "#ffffff";
					ctx.beginPath();
					ctx.arc(p.x, p.y, outerR, 0, Math.PI * 2);
					ctx.fill();

					ctx.fillStyle = series.color;
					ctx.beginPath();
					ctx.arc(p.x, p.y, innerR, 0, Math.PI * 2);
					ctx.fill();

					// Hiển thị nhãn số trực tiếp trên điểm (khi ít đường hoặc tại điểm cuối)
					if (
						seriesList.length <= 3 &&
						(i % showEveryVal === 0 || i === pts.length - 1) &&
						(isSingleSeries || p.rawValue > 0)
					) {
						ctx.fillStyle = series.color;
						ctx.font = `600 10px ${FONT_FAMILY}`;
						ctx.textAlign = "center";
						const lblText = isNormalized
							? `${p.rawValue} (${p.pctValue}%)`
							: String(p.rawValue);
						ctx.fillText(lblText, p.x, p.y - 8);
					}
				}
			}

			// 4. Nhãn trục X (Mốc thời gian)
			ctx.fillStyle = TEXT_COLOR;
			ctx.font = `500 11px ${FONT_FAMILY}`;
			ctx.textAlign = "center";
			const maxLabels = Math.min(periods.length, 10);
			const labelStep = Math.max(1, Math.ceil(periods.length / maxLabels));
			for (let i = 0; i < periods.length; i += labelStep) {
				const label = periods[i].replace(/^\d{4}-/, "");
				ctx.fillText(label, getX(i), plotY + plotH + 22);
			}
			if (periods.length > 1 && (periods.length - 1) % labelStep !== 0) {
				const lastIdx = periods.length - 1;
				ctx.fillText(periods[lastIdx].replace(/^\d{4}-/, ""), getX(lastIdx), plotY + plotH + 22);
			}

			ctx.restore();
		};

		renderScene(null);

		// 5. Gắn sự kiện tương tác Hover & Click-to-Pin để giữ Box số lượng bài viết + mở Popup danh sách bài viết
		if (periods.length === 0 || seriesList.length === 0) return;

		const plotX = CHART_PADDING.left;
		const plotW = containerWidth - CHART_PADDING.left - CHART_PADDING.right;
		const xStep = periods.length > 1 ? plotW / (periods.length - 1) : plotW / 2;

		let pinnedIdx: number | null = null;
		let activeSeriesKey: string | null = null;

		const getIndexFromEvent = (ev: MouseEvent): number => {
			const rect = canvas.getBoundingClientRect();
			const mouseX = ev.clientX - rect.left;
			if (periods.length <= 1) return 0;
			const raw = Math.round((mouseX - plotX) / xStep);
			return Math.max(0, Math.min(periods.length - 1, raw));
		};

		const closePinnedState = () => {
			pinnedIdx = null;
			activeSeriesKey = null;
			postsPopupEl.addClass("is-hidden");
			postsPopupEl.empty();
			tooltipEl.removeClass("is-pinned");
			tooltipEl.addClass("is-hidden");
			renderScene(null);
		};

		const openPostsPopupForSeries = (idx: number, series: TimelineSeries, tooltipLeftPx: number, tooltipWidthPx: number) => {
			activeSeriesKey = series.key;
			const posts = this.engagementStore.queryTimelinePeriodPosts({
				targetPeriod: periods[idx],
				seriesKey: series.key,
				groupBy: this.dateRange.groupBy || "day",
				days: this.dateRange.presetId === "all" ? 0 : 90,
				startDate: this.dateRange.startDate || undefined,
				endDate: this.dateRange.endDate || undefined,
				dateBasis: this.dateRange.dateBasis || "published",
				sourceFilters: this.selectedSources,
				filterAudiences: this.selectedAudiences,
			});

			postsPopupEl.empty();
			postsPopupEl.removeClass("is-hidden");

			const popHeader = postsPopupEl.createDiv({ cls: "cc-chart-posts-header" });
			const popTitleGroup = popHeader.createDiv({ cls: "cc-chart-posts-title-group" });
			const popTopRow = popTitleGroup.createDiv({ cls: "cc-chart-posts-title" });
			const dot = popTopRow.createSpan({ cls: "cc-legend-dot" });
			dot.style.backgroundColor = series.color;
			popTopRow.createSpan({ text: `${series.label} (${posts.length} bài)` });
			popTitleGroup.createDiv({
				cls: "cc-chart-posts-sub",
				text: `Kỳ: ${periods[idx]} • Bấm vào bài để xem trong bảng Danh sách bài viết`,
			});

			const btnClosePop = popHeader.createEl("button", {
				cls: "content-compass-icon-btn cc-chart-posts-close",
				attr: { type: "button", title: "Đóng danh sách bài viết" },
			});
			setIcon(btnClosePop.createSpan({ cls: "cc-icon" }), "x");
			btnClosePop.addEventListener("click", (e) => {
				e.stopPropagation();
				activeSeriesKey = null;
				postsPopupEl.addClass("is-hidden");
				tooltipEl.querySelectorAll(".cc-tooltip-post-count-link").forEach((el) => {
					el.removeClass("is-active");
				});
			});

			const listEl = postsPopupEl.createDiv({ cls: "cc-chart-posts-list" });
			if (posts.length === 0) {
				listEl.createDiv({
					cls: "cc-multiselect-empty",
					text: "Không có bài viết nào trong mốc này.",
				});
			} else {
				for (const post of posts) {
					const itemRow = listEl.createDiv({ cls: "cc-chart-post-item" });
					itemRow.setAttribute(
						"title",
						`Bấm để nhảy tới bài viết này ở bảng Danh sách bài viết đã thu thập:\n${post.titleSnippet}`
					);

					const topLine = itemRow.createDiv({ cls: "cc-chart-post-headline-row" });
					const shortTitle =
						post.titleSnippet.length > 82
							? post.titleSnippet.slice(0, 79) + "..."
							: post.titleSnippet;
					topLine.createSpan({ cls: "cc-chart-post-headline", text: shortTitle });
					const jumpIcon = topLine.createSpan({ cls: "cc-icon cc-chart-post-jump-icon" });
					setIcon(jumpIcon, "arrow-up-right");

					const metaLine = itemRow.createDiv({ cls: "cc-chart-post-meta-row" });
					metaLine.createSpan({
						cls: `content-compass-source-pill ${post.sourceType === "own" ? "is-own" : ""}`,
						text: formatSourceTypeLabel(post.sourceType),
					});
					metaLine.createSpan({
						cls: "cc-chart-post-author",
						text: post.authorName,
					});
					metaLine.createSpan({
						cls: "cc-chart-post-metrics",
						text: `Score ${post.score.toLocaleString("vi-VN")} (👍${post.likes} • 💬${post.comments} • ↗${post.shares})`,
					});

					itemRow.addEventListener("click", (e) => {
						e.stopPropagation();
						closePinnedState();
						if (this.onSelectPost) {
							this.onSelectPost(post);
						}
					});
				}
			}

			// Căn vị trí Popup danh sách bài viết ngay bên cạnh (hoặc bên dưới) hộp Tooltip đang ghim
			const popupW = 330;
			let popLeft = tooltipLeftPx + tooltipWidthPx + 8;
			let popTop = 14;
			if (popLeft + popupW > containerWidth - 6) {
				if (tooltipLeftPx - popupW - 8 >= 6) {
					popLeft = tooltipLeftPx - popupW - 8;
				} else {
					popLeft = Math.max(8, Math.min(containerWidth - popupW - 8, tooltipLeftPx));
					popTop = Math.min(CHART_HEIGHT - 160, (tooltipEl.offsetHeight || 86) + 24);
				}
			}
			postsPopupEl.style.left = `${popLeft}px`;
			postsPopupEl.style.top = `${popTop}px`;
		};

		const renderTooltipBox = (idx: number, isPinned: boolean) => {
			tooltipEl.empty();
			tooltipEl.removeClass("is-hidden");
			tooltipEl.toggleClass("is-pinned", isPinned);

			const pointX = periods.length === 1 ? plotX + plotW / 2 : plotX + xStep * idx;
			const tooltipW = 228;
			const leftPos =
				pointX + tooltipW + 24 > containerWidth
					? Math.max(8, pointX - tooltipW - 12)
					: pointX + 12;
			tooltipEl.style.left = `${leftPos}px`;
			tooltipEl.style.top = `14px`;

			tooltipEl.createDiv({
				cls: "cc-tooltip-title",
				text: `Kỳ: ${periods[idx]}`,
			});

			for (const s of seriesList) {
				const pt = s.points[idx];
				if (!pt) continue;
				const sMax = Math.max(...s.points.map((x) => x.value), 1);
				const pct = Math.round((pt.value / sMax) * 100);
				const row = tooltipEl.createDiv({ cls: "cc-tooltip-row" });
				const left = row.createDiv({ cls: "cc-tooltip-series" });
				const dot = left.createSpan({ cls: "cc-legend-dot" });
				dot.style.backgroundColor = s.color;
				left.createSpan({ text: s.label, attr: { title: s.label } });

				const rightGroup = row.createDiv({ cls: "cc-tooltip-right-group" });
				const valText =
					this.yAxisMode === "normalized"
						? `${pt.value.toLocaleString("vi-VN")} (${pct}%)`
						: pt.value.toLocaleString("vi-VN");
				rightGroup.createSpan({ cls: "cc-tooltip-val", text: valText });

				if (pt.recordCount > 0) {
					const countLink = rightGroup.createSpan({
						cls: `cc-tooltip-post-count-link ${activeSeriesKey === s.key ? "is-active" : ""}`,
						text: `(${pt.recordCount} bài)`,
					});
					const showSeriesPosts = () => {
						pinnedIdx = idx;
						tooltipEl.addClass("is-pinned");
						tooltipEl.querySelectorAll(".cc-tooltip-post-count-link").forEach((el) => {
							el.removeClass("is-active");
						});
						countLink.addClass("is-active");
						openPostsPopupForSeries(idx, s, leftPos, tooltipW);
					};
					countLink.addEventListener("mouseenter", () => {
						if (activeSeriesKey !== s.key || postsPopupEl.hasClass("is-hidden")) {
							showSeriesPosts();
						}
					});
					countLink.addEventListener("click", (e) => {
						e.stopPropagation();
						showSeriesPosts();
					});
				} else {
					rightGroup.createSpan({
						cls: "cc-tooltip-post-count-zero",
						text: "(0 bài)",
					});
				}
			}
		};

		canvas.onmousemove = (ev: MouseEvent) => {
			if (pinnedIdx !== null) return;
			const idx = getIndexFromEvent(ev);
			renderScene(idx);
			renderTooltipBox(idx, false);
		};

		canvas.onmouseleave = () => {
			if (pinnedIdx !== null) return;
			tooltipEl.addClass("is-hidden");
			renderScene(null);
		};

		canvas.onclick = (ev: MouseEvent) => {
			ev.stopPropagation();
			if (pinnedIdx !== null) {
				// Đang ghim mà click ra vùng đồ thị bên ngoài hộp Tooltip/Popup thì đóng hộp ghim
				closePinnedState();
				return;
			}
			const idx = getIndexFromEvent(ev);
			pinnedIdx = idx;
			activeSeriesKey = null;
			postsPopupEl.addClass("is-hidden");
			renderScene(idx);
			renderTooltipBox(idx, true);
		};

		const onDocMouseDown = (evt: MouseEvent) => {
			if (pinnedIdx === null) return;
			const target = evt.target as Node;
			if (tooltipEl.contains(target) || postsPopupEl.contains(target) || canvas.contains(target)) {
				return;
			}
			closePinnedState();
		};
		document.addEventListener("mousedown", onDocMouseDown);
		this.outsideClickCleanup = () => {
			document.removeEventListener("mousedown", onDocMouseDown);
		};
	}

	private hexToRgba(hex: string, alpha: number): string {
		const clean = hex.replace("#", "");
		if (clean.length !== 6) return `rgba(10, 132, 255, ${alpha})`;
		const r = parseInt(clean.slice(0, 2), 16);
		const g = parseInt(clean.slice(2, 4), 16);
		const b = parseInt(clean.slice(4, 6), 16);
		return `rgba(${r}, ${g}, ${b}, ${alpha})`;
	}
}
