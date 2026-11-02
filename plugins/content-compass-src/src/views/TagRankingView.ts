/**
 * Ten file: TagRankingView.ts
 * Last update: 02/11/2026 17:40 (GMT+7)
 * Vai tro: Render Bang Xep hang Hieu suat Da chieu (Top Bai viet, Theo Nguon Trang, Theo Tag/Hashtag,
 *          Theo Audience, Theo Pillar) bang Canvas HiDPI.
 * Duoc su dung khi nao?: Khi tab Analytics duoc hien thi tren Dashboard.
 * Output: Bo chon 5 chieu phan tich + Bo loc Chi so (Score/TB Score/Likes/Comments/Shares), Phan loai nguon,
 *         Top N, Khoang thoi gian + Bieu do thanh ngang chuan Apple Screen Time.
 * Tom tat logic hoat dong: Truy van EngagementStore.queryRankingAdvanced, ve thanh ngang bo tron kem
 *          chi tiet phan ra (Score, Likes, Comments, Shares, So bai) cho tung hang muc.
 */

import { setIcon } from "obsidian";
import {
	EngagementStore,
	TagRankEntry,
	RankingDimension,
	ChartMetricType,
} from "../data/EngagementStore";
import {
	DateRangeSelection,
	computeRangeForPreset,
	renderDateRangePickerButton,
} from "./DateRangePickerPopover";

// Nhom 1: Hang so ve bieu do chuan Apple System Colors
const BAR_HEIGHT = 26;
const BAR_GAP = 10;
const CHART_PADDING = { top: 12, right: 175, bottom: 12, left: 275 };
const BAR_COLORS = [
	"#0a84ff", // Apple System Blue
	"#5e5ce6", // Apple System Indigo
	"#30d158", // Apple System Green
	"#ff9f0a", // Apple System Orange
	"#ff375f", // Apple System Pink
];
const TEXT_COLOR = "hsla(0, 0%, 58%, 0.95)";
const TRACK_COLOR = "hsla(0, 0%, 50%, 0.08)";
const FONT_FAMILY = '-apple-system, BlinkMacSystemFont, "SF Pro Text", "Inter", sans-serif';

// Nhom 2: Lop TagRankingView (Multi-Dimension Performance Ranking)
export class TagRankingView {
	private container: HTMLElement;
	private engagementStore: EngagementStore;

	private dimension: RankingDimension = "tag";
	private metric: Exclude<ChartMetricType, "posts"> = "score";
	private dateRange: DateRangeSelection = {
		presetId: "90d",
		...computeRangeForPreset("90d"),
		dateBasis: "published",
	};
	private limit: number = 10;
	private sourceFilter: string = "all";

	constructor(container: HTMLElement, engagementStore: EngagementStore) {
		this.container = container;
		this.engagementStore = engagementStore;
	}

	// Nhom 3: Render toan bo view voi Bo chon 5 Chieu + Bo loc Chi so & Khoang thoi gian (Popover 3 cot)
	public render(): void {
		this.container.empty();

		const card = this.container.createDiv({ cls: "content-compass-card" });

		// 1. Header: Tieu de + Nut mo Popover Chon Thoi gian 3 Cot
		const header = card.createDiv({ cls: "content-compass-card-header" });
		const title = header.createDiv({ cls: "content-compass-card-title" });
		const titleIcon = title.createSpan({ cls: "cc-icon" });
		setIcon(titleIcon, "bar-chart-2");
		title.createSpan({ text: "Bảng Xếp hạng Hiệu suất Đa chiều" });

		if (!this.engagementStore.hasData()) {
			const placeholder = card.createDiv({ cls: "content-compass-placeholder" });
			placeholder.setText("Chưa có dữ liệu engagement. Hãy quét hoặc nhập dữ liệu ở bảng trên.");
			return;
		}

		renderDateRangePickerButton(
			header,
			this.dateRange,
			{ showGroupBy: false, showDateBasis: true },
			(next) => {
				this.dateRange = next;
				this.render();
			}
		);

		// 2. Dai Bo loc Da chieu (Chieu phan tich + Chi so xep hang + Nguon + Top N)
		const filterStrip = card.createDiv({ cls: "content-compass-chart-filter-strip" });

		// Segmented Pill: 5 Chieu Xep hang (Theo Tag/Chu de | Top Bai viet | Theo Trang | Audience | Pillar)
		const dimSeg = filterStrip.createDiv({ cls: "content-compass-segmented-control" });
		const dims: Array<{ id: RankingDimension; label: string }> = [
			{ id: "tag", label: "Theo Tag / Chủ đề" },
			{ id: "post", label: "Top Bài viết" },
			{ id: "author", label: "Theo Trang / Tác giả" },
			{ id: "audience", label: "Theo Audience" },
			{ id: "pillar", label: "Theo Pillar" },
		];
		for (const d of dims) {
			const b = dimSeg.createEl("button", {
				cls: `content-compass-tab-btn ${this.dimension === d.id ? "is-active" : ""}`,
				text: d.label,
			});
			b.addEventListener("click", () => {
				this.dimension = d.id;
				this.render();
			});
		}

		// Chọn chỉ số xếp hạng
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
			this.render();
		});

		// Chọn Nguồn (Tất cả / Thương hiệu / Đối thủ)
		const sourceSelect = filterStrip.createEl("select");
		sourceSelect.createEl("option", { value: "all", text: "Nguồn: Tất cả" });
		sourceSelect.createEl("option", { value: "own", text: "Chỉ Thương hiệu" });
		sourceSelect.createEl("option", { value: "external", text: "Chỉ Đối thủ / Bên ngoài" });
		sourceSelect.value = this.sourceFilter;
		sourceSelect.addEventListener("change", () => {
			this.sourceFilter = sourceSelect.value;
			this.render();
		});

		// Chọn số lượng Top N
		const limitSelect = filterStrip.createEl("select");
		for (const n of [5, 10, 15, 25]) {
			limitSelect.createEl("option", { value: String(n), text: `Hiển thị: Top ${n}` });
		}
		limitSelect.value = String(this.limit);
		limitSelect.addEventListener("change", () => {
			this.limit = parseInt(limitSelect.value) || 10;
			this.render();
		});

		// 3. Canvas vẽ biểu đồ thanh ngang
		const data = this.engagementStore.queryRankingAdvanced({
			dimension: this.dimension,
			metric: this.metric,
			days: this.dateRange.presetId === "all" ? 0 : 90,
			startDate: this.dateRange.startDate || undefined,
			endDate: this.dateRange.endDate || undefined,
			dateBasis: this.dateRange.dateBasis || "published",
			limit: this.limit,
			sourceFilter: this.sourceFilter,
		});

		const canvasWrap = card.createDiv({ cls: "content-compass-canvas-wrap" });
		const canvas = canvasWrap.createEl("canvas", { cls: "content-compass-chart-canvas" });

		requestAnimationFrame(() => {
			this.drawChart(canvas, data);
		});
	}

	// Nhom 4: Ve bieu do horizontal bar chart chuan Apple Screen Time
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
					: "Không có dữ liệu cho chiều phân tích và khoảng thời gian này";
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
			const barWidth = Math.max((entry.value / maxVal) * plotW, 8);
			const color = BAR_COLORS[i % BAR_COLORS.length];
			const radius = 7;

			// Rãnh nền mờ kiểu iOS Screen Time
			ctx.fillStyle = TRACK_COLOR;
			ctx.beginPath();
			ctx.roundRect(plotX, y, plotW, BAR_HEIGHT, radius);
			ctx.fill();

			// Thanh giá trị chính bo tròn
			ctx.fillStyle = color;
			ctx.beginPath();
			ctx.roundRect(plotX, y, barWidth, BAR_HEIGHT, radius);
			ctx.fill();

			// Nhãn hạng mục bên trái
			ctx.fillStyle = TEXT_COLOR;
			ctx.font = `500 12px ${FONT_FAMILY}`;
			ctx.textAlign = "right";
			let rawLabel = entry.sublabel ? `[${entry.sublabel}] ${entry.tag}` : entry.tag;
			if (rawLabel.length > 42) rawLabel = rawLabel.slice(0, 40) + "...";
			ctx.fillText(rawLabel, plotX - 10, y + BAR_HEIGHT / 2 + 4);

			// Điểm số chính + phân rã chi tiết bên phải
			ctx.fillStyle = color;
			ctx.font = `650 12px ${FONT_FAMILY}`;
			ctx.textAlign = "left";
			const mainValStr = this.formatNumber(entry.value);
			ctx.fillText(mainValStr, plotX + barWidth + 8, y + BAR_HEIGHT / 2 + 4);

			const mainValWidth = ctx.measureText(mainValStr).width;
			ctx.fillStyle = TEXT_COLOR;
			ctx.font = `500 11px ${FONT_FAMILY}`;
			const detailStr =
				this.dimension === "post"
					? `(${entry.likes}L · ${entry.comments}C · ${entry.shares}S)`
					: `(${entry.postCount} bài · ${entry.likes}L · ${entry.comments}C)`;
			ctx.fillText(detailStr, plotX + barWidth + 14 + mainValWidth, y + BAR_HEIGHT / 2 + 4);
		}
	}

	private formatNumber(n: number): string {
		if (n >= 1000) return (n / 1000).toFixed(1) + "k";
		return String(n);
	}
}
