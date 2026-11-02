/**
 * Ten file: PillarMapView.ts
 * Last update: 24/10/2026 15:00 (GMT+7)
 * Vai tro: Renderer cho goc nhin Treemap (Pillar Map) trong tab Strategy.
 * Duoc su dung khi nao?: Khi tab Strategy duoc hien thi tren Dashboard.
 * Output: Giao dien Treemap 2D, dien tich ty le voi engagement score (fallback topicCount).
 * Tom tat logic hoat dong: Lay du lieu tu TagIndex, AudienceIndex, EngagementStore, tinh weight
 * (uu tien engagement, fallback topicCount), ap dung Squarified Treemap, render khoi pillar.
 */

import { App, setIcon } from "obsidian";
import { TagIndex } from "../data/TagIndex";
import { AudienceIndex } from "../data/AudienceIndex";
import { EngagementStore } from "../data/EngagementStore";

// Nhom 1: Bang mau Apple System Colors dai dien cho cac Tru cot noi dung
const PILLAR_COLOR_PALETTES = [
	{ border: "rgba(10, 132, 255, 0.38)", bg: "rgba(10, 132, 255, 0.09)", text: "#0a84ff" },
	{ border: "rgba(94, 92, 230, 0.38)",  bg: "rgba(94, 92, 230, 0.09)",  text: "#5e5ce6" },
	{ border: "rgba(48, 209, 88, 0.38)",  bg: "rgba(48, 209, 88, 0.09)",  text: "#30d158" },
	{ border: "rgba(255, 159, 10, 0.38)", bg: "rgba(255, 159, 10, 0.09)", text: "#ff9f0a" },
	{ border: "rgba(255, 55, 95, 0.38)",  bg: "rgba(255, 55, 95, 0.09)",  text: "#ff375f" },
];

// Nhom 1b: Khoang cach pixel giua cac khoi Bento Treemap
const TREEMAP_GAP_PX = 8;

// Nhom 2: Cau truc hinh chu nhat cho thuat toan treemap
interface TRect {
	x: number; // % tu trai
	y: number; // % tu tren
	w: number; // % chieu rong
	h: number; // % chieu cao
}

interface TItem {
	weight: number;
	originalIndex: number;
}

// Nhom 3: Thuat toan Squarified Treemap
// Chia hinh chu nhat thanh cac hinh chu nhat con co dien tich ty le voi weight,
// toi uu aspect ratio (gan hinh vuong nhat co the).
function squarifiedLayout(weights: number[]): TRect[] {
	const rects: TRect[] = new Array(weights.length);
	const items: TItem[] = weights.map((w, i) => ({ weight: Math.max(w, 1), originalIndex: i }));

	squarifyRecursive(items, { x: 0, y: 0, w: 100, h: 100 }, rects);
	return rects;
}

function squarifyRecursive(items: TItem[], rect: TRect, out: TRect[]): void {
	if (items.length === 0) return;

	// Truong hop co so: 1 item chiem toan bo hinh chu nhat
	if (items.length === 1) {
		out[items[0].originalIndex] = { ...rect };
		return;
	}

	// Sap xep giam dan theo weight
	const sorted = [...items].sort((a, b) => b.weight - a.weight);
	const totalWeight = sorted.reduce((s, it) => s + it.weight, 0);

	// Chon huong chia: doc theo canh ngan hon de toi uu aspect ratio
	const isWide = rect.w >= rect.h;
	const side = isWide ? rect.h : rect.w;   // canh ngan
	const length = isWide ? rect.w : rect.h;  // canh dai

	// Xay dung hang (row): them item cho den khi aspect ratio xau di
	let bestRow: TItem[] = [];
	let bestWorst = Infinity;
	let bestRowWeight = 0;

	const row: TItem[] = [];
	let rowWeight = 0;

	for (let i = 0; i < sorted.length; i++) {
		row.push(sorted[i]);
		rowWeight += sorted[i].weight;

		// Tinh worst aspect ratio cua hang hien tai
		const rowLength = (rowWeight / totalWeight) * length;
		let worst = 0;
		for (const item of row) {
			const itemSide = (item.weight / rowWeight) * side;
			const ar = Math.max(rowLength / itemSide, itemSide / rowLength);
			if (ar > worst) worst = ar;
		}

		if (worst <= bestWorst) {
			bestWorst = worst;
			bestRow = [...row];
			bestRowWeight = rowWeight;
		} else {
			// Them item lam xau di → dung lai, dung hang truoc do
			break;
		}
	}

	// Dat vi tri cho cac item trong hang tot nhat
	const bestRowLength = (bestRowWeight / totalWeight) * length;
	let offset = 0;

	for (const item of bestRow) {
		const itemSide = (item.weight / bestRowWeight) * side;
		if (isWide) {
			out[item.originalIndex] = { x: rect.x, y: rect.y + offset, w: bestRowLength, h: itemSide };
		} else {
			out[item.originalIndex] = { x: rect.x + offset, y: rect.y, w: itemSide, h: bestRowLength };
		}
		offset += itemSide;
	}

	// De quy tren phan hinh chu nhat con lai
	const remaining = sorted.slice(bestRow.length);
	if (remaining.length > 0) {
		let nextRect: TRect;
		if (isWide) {
			nextRect = { x: rect.x + bestRowLength, y: rect.y, w: rect.w - bestRowLength, h: rect.h };
		} else {
			nextRect = { x: rect.x, y: rect.y + bestRowLength, w: rect.w, h: rect.h - bestRowLength };
		}
		squarifyRecursive(remaining, nextRect, out);
	}
}

// Nhom 4: Lop hien thi ban do tru cot PillarMapView
export class PillarMapView {
	private container: HTMLElement;
	private tagIndex: TagIndex;
	private audienceIndex: AudienceIndex;
	private app: App;
	private engagementStore: EngagementStore | null;

	constructor(container: HTMLElement, tagIndex: TagIndex, audienceIndex: AudienceIndex, app: App, engagementStore?: EngagementStore) {
		this.container = container;
		this.tagIndex = tagIndex;
		this.audienceIndex = audienceIndex;
		this.app = app;
		this.engagementStore = engagementStore || null;
	}

	// Nhom 5: Phuong thuc dung giao dien Treemap 2D
	public render(): void {
		this.container.empty();

		const card = this.container.createDiv({ cls: "content-compass-card" });
		const title = card.createDiv({ cls: "content-compass-card-title" });
		const titleIcon = title.createSpan({ cls: "cc-icon" });
		setIcon(titleIcon, "layout-grid");
		title.createSpan({ text: "Bản đồ Trụ cột Nội dung (Pillar Treemap)" });

		const pillars = this.tagIndex.getPillars();
		if (pillars.size === 0) {
			const emptyMsg = card.createDiv({ cls: "content-compass-placeholder" });
			emptyMsg.setText("Chưa nạp được danh mục Pillar từ topic_map.yaml");
			return;
		}

		const totalTopics = this.tagIndex.getTotalTopicCount() || 1;
		const treemap = card.createDiv({ cls: "content-compass-treemap" });

		// Thu thap du lieu Pillar theo thu tu goc
		const pillarEntries = Array.from(pillars.entries());
		// Xac dinh nguon weight: uu tien engagement, fallback topicCount
		const useEngagement = this.engagementStore?.hasData() ?? false;
		const weights = pillarEntries.map(([pillarName, p]) => {
			if (useEngagement) {
				return this.engagementStore!.getScoreByPillar(pillarName) || 1;
			}
			return p.topicIds.length || 1;
		});

		// Tinh layout bang thuat toan Squarified Treemap
		const rects = squarifiedLayout(weights);

		// Render tung khoi Pillar tai vi tri da tinh
		for (let idx = 0; idx < pillarEntries.length; idx++) {
			const [pillarName, pillarNode] = pillarEntries[idx];
			const palette = PILLAR_COLOR_PALETTES[idx % PILLAR_COLOR_PALETTES.length];
			const rect = rects[idx];

			const topicCount = pillarNode.topicIds.length || 1;
			const pillarPercent = Math.round((topicCount / totalTopics) * 100);

			// Khoi Pillar: position absolute, vi tri va kich thuoc tinh bang %
			const pillarBlock = treemap.createDiv({ cls: "content-compass-treemap-pillar" });
			pillarBlock.style.borderColor = palette.border;
			pillarBlock.style.backgroundColor = palette.bg;

			// Gan vi tri voi gap pixel de tao khoang cach giua cac khoi
			const g = TREEMAP_GAP_PX;
			pillarBlock.style.left = `calc(${rect.x}% + ${g / 2}px)`;
			pillarBlock.style.top = `calc(${rect.y}% + ${g / 2}px)`;
			pillarBlock.style.width = `calc(${rect.w}% - ${g}px)`;
			pillarBlock.style.height = `calc(${rect.h}% - ${g}px)`;

			// Header Tru cot
			const pillarHeader = pillarBlock.createDiv({ cls: "content-compass-treemap-pillar-title" });
			pillarHeader.style.color = palette.text;
			pillarHeader.setText(`${pillarName}`);

			const statsBadge = pillarHeader.createSpan({ cls: "content-compass-treemap-badge" });
			if (useEngagement) {
				const score = this.engagementStore!.getScoreByPillar(pillarName);
				statsBadge.setText(`${topicCount} topics \u2022 Score: ${score} \u2022 ${pillarNode.audienceSlugs.length} audiences`);
			} else {
				statsBadge.setText(`${topicCount} topics (${pillarPercent}%) \u2022 ${pillarNode.audienceSlugs.length} audiences`);
			}

			// Container chua cac cell Audience thuoc Pillar
			const cellsContainer = pillarBlock.createDiv({ cls: "content-compass-treemap-cells" });

			if (pillarNode.audienceSlugs.length === 0) {
				const emptyCell = cellsContainer.createDiv({ cls: "content-compass-placeholder" });
				emptyCell.setText("Chưa có audience liên kết");
				continue;
			}

			// Dem so topic trong pillar nay lien quan den tung audience
			const audienceTopicMap = new Map<string, number>();
			for (const tId of pillarNode.topicIds) {
				const tNode = this.tagIndex.getTopics().get(tId);
				if (tNode) {
					for (const aSlug of tNode.audienceSlugs) {
						audienceTopicMap.set(aSlug, (audienceTopicMap.get(aSlug) || 0) + 1);
					}
				}
			}

			for (const aSlug of pillarNode.audienceSlugs) {
				const aNode = this.audienceIndex.getNode(aSlug);
				const aTopicCount = audienceTopicMap.get(aSlug) || 1;
				const cell = cellsContainer.createDiv({ cls: "content-compass-treemap-cell" });

				// Audience cell hien thi kich thuoc tu nhien (khong can flex-grow)

				const label = aNode ? aNode.displayName : aSlug;
				const level = aNode ? aNode.level : "unknown";
				const isBuyer = aNode ? aNode.isBuyerJob : false;

				if (isBuyer) {
					cell.addClass("is-buyer");
					const buyerBadge = cell.createSpan({ cls: "content-compass-buyer-pill" });
					buyerBadge.setText("BUYER");
				}

				const textSpan = cell.createSpan({ text: label });
				textSpan.addClass("content-compass-treemap-cell-text");

				const countBadge = cell.createSpan({ cls: "content-compass-cell-count" });
				countBadge.setText(`${aTopicCount}t`);

				// Tooltip hien thi da thong tin
				cell.setAttribute(
					"title",
					`Audience: ${label}\nCấp bậc: ${level.toUpperCase()}\nSố chủ đề trong Pillar: ${aTopicCount} topics\nBuyer Job: ${isBuyer ? "CÓ" : "KHÔNG"}\nNhấp để mở note`
				);

				// Nhap chuot de mo note Audience tuong ung trong vault
				cell.addEventListener("click", () => {
					this.app.workspace.openLinkText(aSlug, "");
				});
			}
		}
	}
}
