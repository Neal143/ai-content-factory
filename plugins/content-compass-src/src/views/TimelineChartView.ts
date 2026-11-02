/**
 * Ten file: TimelineChartView.ts
 * Last update: 02/11/2026 17:38 (GMT+7)
 * Vai tro: Render bang phan tich xu huong Engagement da chieu (KPI Summary Tiles + Interactive HiDPI Line Chart).
 * Duoc su dung khi nao?: Khi tab Analytics duoc hien thi tren Dashboard.
 * Output: 4 the KPI Summary chuan Apple Health + Bo loc 6 chieu (Don vi Ngay/Tuan/Thang, Khoang thoi gian,
 *         Chi so Score/Likes/Comments/Shares/Avg/Posts, Nguon Trang, Truc ngay dang/ngay quet, Audience) + Canvas Chart.
 * Tom tat logic hoat dong: Truy van du lieu qua EngagementStore.queryTimelineAdvanced, cap nhat tuc thoi KPI va ve
 *          duong xu huong kem dai mau chuyen sac theo dung mau sac cua chi so dang chon.
 */

import { setIcon } from "obsidian";
import {
	EngagementStore,
	TimelinePoint,
	ChartMetricType,
} from "../data/EngagementStore";
import { AudienceIndex } from "../data/AudienceIndex";
import {
	DateRangeSelection,
	computeRangeForPreset,
	renderDateRangePickerButton,
} from "./DateRangePickerPopover";

// Nhom 1: Hang so ve bieu do chuan Apple Stocks / Health
const CHART_HEIGHT = 250;
const CHART_PADDING = { top: 28, right: 38, bottom: 40, left: 56 };
const GRID_COLOR = "hsla(0, 0%, 50%, 0.14)";
const TEXT_COLOR = "hsla(0, 0%, 58%, 0.95)";
const FONT_FAMILY = '-apple-system, BlinkMacSystemFont, "SF Pro Text", "Inter", sans-serif';

const METRIC_THEMES: Record<ChartMetricType, { line: string; fillTop: string; fillBottom: string; label: string }> = {
	score: {
		line: "#0a84ff",
		fillTop: "rgba(10, 132, 255, 0.26)",
		fillBottom: "rgba(10, 132, 255, 0.0)",
		label: "Điểm Score",
	},
	avg_score: {
		line: "#0a84ff",
		fillTop: "rgba(10, 132, 255, 0.24)",
		fillBottom: "rgba(10, 132, 255, 0.0)",
		label: "TB Score/bài",
	},
	likes: {
		line: "#5e5ce6",
		fillTop: "rgba(94, 92, 230, 0.26)",
		fillBottom: "rgba(94, 92, 230, 0.0)",
		label: "Lượt thích",
	},
	comments: {
		line: "#30d158",
		fillTop: "rgba(48, 209, 88, 0.26)",
		fillBottom: "rgba(48, 209, 88, 0.0)",
		label: "Bình luận",
	},
	shares: {
		line: "#ff9f0a",
		fillTop: "rgba(255, 159, 10, 0.26)",
		fillBottom: "rgba(255, 159, 10, 0.0)",
		label: "Chia sẻ",
	},
	posts: {
		line: "#ff375f",
		fillTop: "rgba(255, 55, 95, 0.24)",
		fillBottom: "rgba(255, 55, 95, 0.0)",
		label: "Số bài viết",
	},
};

// Nhom 2: Lop TimelineChartView
export class TimelineChartView {
	private container: HTMLElement;
	private engagementStore: EngagementStore;
	private audienceIndex: AudienceIndex;

	private dateRange: DateRangeSelection = {
		presetId: "90d",
		...computeRangeForPreset("90d"),
		groupBy: "day",
		dateBasis: "published",
	};
	private metric: ChartMetricType = "score";
	private sourceFilter: string = "all";
	private filterAudience: string = "";

	constructor(container: HTMLElement, engagementStore: EngagementStore, audienceIndex: AudienceIndex) {
		this.container = container;
		this.engagementStore = engagementStore;
		this.audienceIndex = audienceIndex;
	}

	// Nhom 3: Render toan bo view voi Header (Tich hop Popover 3 cot) + Filter Strip + KPI Cards + Canvas
	public render(): void {
		this.container.empty();

		const card = this.container.createDiv({ cls: "content-compass-card" });

		// 1. Header: Tieu de + Nut mo Popover Chon Thoi gian 3 Cot (Tich hop luon Dropdown Xem theo Ngay/Tuan/Thang/Nam)
		const header = card.createDiv({ cls: "content-compass-card-header" });
		const title = header.createDiv({ cls: "content-compass-card-title" });
		const titleIcon = title.createSpan({ cls: "cc-icon" });
		setIcon(titleIcon, "trending-up");
		title.createSpan({ text: "Xu hướng Engagement theo thời gian" });

		if (!this.engagementStore.hasData()) {
			const placeholder = card.createDiv({ cls: "content-compass-placeholder" });
			placeholder.setText("Chưa có dữ liệu engagement. Hãy quét hoặc nhập dữ liệu ở bảng trên.");
			return;
		}

		renderDateRangePickerButton(
			header,
			this.dateRange,
			{ showGroupBy: true, showDateBasis: true },
			(next) => {
				this.dateRange = next;
				this.render();
			}
		);

		// 2. Dai Bo loc chi tiet (Chi so, Nguon/Trang, Audience)
		const filterStrip = card.createDiv({ cls: "content-compass-chart-filter-strip" });

		// Chọn chỉ số biểu diễn
		const metricSelect = filterStrip.createEl("select");
		metricSelect.setAttribute("title", "Chọn chỉ số hiển thị trên trục Y của biểu đồ");
		const metricOpts: Array<{ val: ChartMetricType; label: string }> = [
			{ val: "score", label: "Chỉ số: Tổng Điểm (Score)" },
			{ val: "avg_score", label: "Chỉ số: Trung bình Score / bài" },
			{ val: "likes", label: "Chỉ số: Lượt thích (Likes)" },
			{ val: "comments", label: "Chỉ số: Bình luận (Comments)" },
			{ val: "shares", label: "Chỉ số: Lượt chia sẻ (Shares)" },
			{ val: "posts", label: "Chỉ số: Số lượng bài viết" },
		];
		for (const m of metricOpts) {
			metricSelect.createEl("option", { value: m.val, text: m.label });
		}
		metricSelect.value = this.metric;
		metricSelect.addEventListener("change", () => {
			this.metric = metricSelect.value as ChartMetricType;
			this.render();
		});

		// Chọn Nguồn (Tất cả / Thương hiệu / Đối thủ / Từng Trang cụ thể)
		const sourceSelect = filterStrip.createEl("select");
		sourceSelect.setAttribute("title", "Lọc theo phân loại nguồn hoặc từng Trang Facebook đang theo dõi");
		sourceSelect.createEl("option", { value: "all", text: "Nguồn: Tất cả các trang" });
		sourceSelect.createEl("option", { value: "own", text: "Nguồn: Chỉ Thương hiệu" });
		sourceSelect.createEl("option", { value: "external", text: "Nguồn: Chỉ Đối thủ / Bên ngoài" });
		for (const author of this.engagementStore.getKnownAuthors()) {
			sourceSelect.createEl("option", { value: `author:${author}`, text: `Trang: ${author}` });
		}
		sourceSelect.value = this.sourceFilter;
		sourceSelect.addEventListener("change", () => {
			this.sourceFilter = sourceSelect.value;
			this.render();
		});

		// Chọn Audience (nếu có trong Vault)
		const audienceSelect = filterStrip.createEl("select");
		audienceSelect.createEl("option", { value: "", text: "Khán giả: Tất cả Audience" });
		const allNodes = this.audienceIndex.getAllNodes();
		for (const node of allNodes.values()) {
			audienceSelect.createEl("option", { value: node.slug, text: `Audience: ${node.displayName}` });
		}
		audienceSelect.value = this.filterAudience;
		audienceSelect.addEventListener("change", () => {
			this.filterAudience = audienceSelect.value;
			this.render();
		});

		// 3. Truy vấn dữ liệu và dựng 4 Thẻ KPI Tóm tắt chuẩn Apple Health (Bấm vào thẻ để đổi chỉ số vẽ)
		const { points, summary } = this.engagementStore.queryTimelineAdvanced({
			groupBy: this.dateRange.groupBy || "day",
			days: this.dateRange.presetId === "all" ? 0 : 90,
			startDate: this.dateRange.startDate || undefined,
			endDate: this.dateRange.endDate || undefined,
			metric: this.metric,
			dateBasis: this.dateRange.dateBasis || "published",
			sourceFilter: this.sourceFilter,
			filterAudience: this.filterAudience || undefined,
		});

		const kpiGrid = card.createDiv({ cls: "content-compass-kpi-grid" });
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
			const tile = kpiGrid.createDiv({
				cls: `content-compass-kpi-tile ${this.metric === item.key ? "is-selected" : ""}`,
			});
			tile.setAttribute("title", `Bấm để vẽ biểu đồ xu hướng theo: ${item.title}`);
			const topRow = tile.createDiv({ cls: "content-compass-kpi-title" });
			const ic = topRow.createSpan({ cls: "cc-icon" });
			ic.style.color = item.color;
			setIcon(ic, item.icon);
			topRow.createSpan({ text: item.title });

			const valEl = tile.createDiv({ cls: "content-compass-kpi-value", text: item.value });
			valEl.style.color = item.color;

			tile.createDiv({ cls: "content-compass-kpi-sub", text: item.sub });
			tile.addEventListener("click", () => {
				this.metric = item.key;
				this.render();
			});
		}

		// 4. Canvas vẽ biểu đồ
		const canvasWrap = card.createDiv({ cls: "content-compass-canvas-wrap" });
		const canvas = canvasWrap.createEl("canvas", { cls: "content-compass-chart-canvas" });
		canvas.height = CHART_HEIGHT;

		requestAnimationFrame(() => {
			this.drawChart(canvas, points);
		});
	}

	// Nhom 4: Ve bieu do line chart len canvas (HiDPI + Khong tran mep phai)
	private drawChart(canvas: HTMLCanvasElement, data: TimelinePoint[]): void {
		const dpr = window.devicePixelRatio || 1;
		const rawParentWidth = canvas.parentElement?.clientWidth || 680;
		const containerWidth = Math.max(rawParentWidth, 320);

		canvas.style.width = `${containerWidth}px`;
		canvas.style.height = `${CHART_HEIGHT}px`;
		canvas.width = Math.floor(containerWidth * dpr);
		canvas.height = Math.floor(CHART_HEIGHT * dpr);

		const ctx = canvas.getContext("2d");
		if (!ctx) return;
		ctx.scale(dpr, dpr);

		ctx.clearRect(0, 0, containerWidth, CHART_HEIGHT);

		if (data.length === 0) {
			ctx.fillStyle = TEXT_COLOR;
			ctx.font = `500 13px ${FONT_FAMILY}`;
			ctx.textAlign = "center";
			ctx.fillText("Không có dữ liệu khớp với bộ lọc đang chọn", containerWidth / 2, CHART_HEIGHT / 2);
			return;
		}

		const theme = METRIC_THEMES[this.metric] || METRIC_THEMES.score;
		const plotX = CHART_PADDING.left;
		const plotY = CHART_PADDING.top;
		const plotW = containerWidth - CHART_PADDING.left - CHART_PADDING.right;
		const plotH = CHART_HEIGHT - CHART_PADDING.top - CHART_PADDING.bottom;

		const maxVal = Math.max(...data.map((d) => d.value), 1);
		const yScale = plotH / maxVal;

		// Vẽ đường lưới ngang nét đứt mảnh chuẩn Apple Health
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
			const val = Math.round((maxVal / 4) * i);
			ctx.fillText(String(val), plotX - 10, y + 4);
		}
		ctx.setLineDash([]);

		const xStep = data.length > 1 ? plotW / (data.length - 1) : plotW / 2;
		const pts = data.map((d, i) => ({
			x: data.length === 1 ? plotX + plotW / 2 : plotX + xStep * i,
			y: plotY + plotH - d.value * yScale,
			value: d.value,
			period: d.period,
			postCount: d.recordCount,
		}));

		// Vẽ vùng Area Gradient bên dưới đường xu hướng
		if (pts.length > 1) {
			const areaGrad = ctx.createLinearGradient(0, plotY, 0, plotY + plotH);
			areaGrad.addColorStop(0, theme.fillTop);
			areaGrad.addColorStop(1, theme.fillBottom);
			ctx.fillStyle = areaGrad;
			ctx.beginPath();
			ctx.moveTo(pts[0].x, plotY + plotH);
			for (const p of pts) ctx.lineTo(p.x, p.y);
			ctx.lineTo(pts[pts.length - 1].x, plotY + plotH);
			ctx.closePath();
			ctx.fill();
		}

		// Vẽ đường chính mịn
		ctx.strokeStyle = theme.line;
		ctx.lineWidth = 2.5;
		ctx.lineJoin = "round";
		ctx.lineCap = "round";
		ctx.beginPath();
		for (let i = 0; i < pts.length; i++) {
			if (i === 0) ctx.moveTo(pts[i].x, pts[i].y);
			else ctx.lineTo(pts[i].x, pts[i].y);
		}
		ctx.stroke();

		// Vẽ điểm dữ liệu kèm viền trắng nổi bật
		const showEveryVal = Math.max(1, Math.ceil(pts.length / 14));
		for (let i = 0; i < pts.length; i++) {
			const p = pts[i];
			ctx.fillStyle = "#ffffff";
			ctx.beginPath();
			ctx.arc(p.x, p.y, 4.5, 0, Math.PI * 2);
			ctx.fill();

			ctx.fillStyle = theme.line;
			ctx.beginPath();
			ctx.arc(p.x, p.y, 3.2, 0, Math.PI * 2);
			ctx.fill();

			if (i % showEveryVal === 0 || i === pts.length - 1) {
				ctx.fillStyle = TEXT_COLOR;
				ctx.font = `600 10.5px ${FONT_FAMILY}`;
				ctx.textAlign = "center";
				ctx.fillText(String(p.value), p.x, p.y - 9);
			}
		}

		// Nhãn trục X
		ctx.fillStyle = TEXT_COLOR;
		ctx.font = `500 11px ${FONT_FAMILY}`;
		ctx.textAlign = "center";
		const maxLabels = Math.min(pts.length, 10);
		const labelStep = Math.max(1, Math.ceil(pts.length / maxLabels));
		for (let i = 0; i < pts.length; i += labelStep) {
			const label = pts[i].period.replace(/^\d{4}-/, "");
			ctx.fillText(label, pts[i].x, plotY + plotH + 22);
		}
		if (pts.length > 1 && (pts.length - 1) % labelStep !== 0) {
			const lastPt = pts[pts.length - 1];
			ctx.fillText(lastPt.period.replace(/^\d{4}-/, ""), lastPt.x, plotY + plotH + 22);
		}
	}
}
