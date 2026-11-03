/**
 * Tên file: PillarHealthView.ts
 * Last update: 03/11/2026 12:20 (GMT+7)
 * Vai trò: Renderer cho biểu đồ tỷ trọng nội dung (Pillar Health) trong tab Strategy.
 * Được sử dụng khi nào?: Trong tab Strategy để trực quan hóa sự cân bằng khối lượng nội dung giữa các Pillar.
 * Output: Biểu đồ thanh ngang (horizontal stacked bar chart), bảng số liệu thống kê chi tiết và nút Hide/Show góc trên cùng bên phải.
 * Tóm tắt logic hoạt động: Tính toán tỷ lệ phần trăm topic và audience thuộc từng Pillar, dựng thanh tiến trình
 * với màu sắc tương ứng và bảng thống kê tổng hợp (Tên Pillar | Số Topics | Số Audiences | % Tỷ trọng).
 */

import { setIcon } from "obsidian";
import { TagIndex } from "../data/TagIndex";
import { AudienceIndex } from "../data/AudienceIndex";

// Nhóm 1: Bảng màu Apple System Colors đồng bộ với Bento Treemap
const PILLAR_COLORS = [
	"#0a84ff",
	"#5e5ce6",
	"#30d158",
	"#ff9f0a",
	"#ff375f",
];

// Nhóm 2: Lớp hiển thị tỷ trọng PillarHealthView
export class PillarHealthView {
	private container: HTMLElement;
	private tagIndex: TagIndex;
	private audienceIndex: AudienceIndex;
	private isCollapsed: boolean = false;

	constructor(container: HTMLElement, tagIndex: TagIndex, audienceIndex: AudienceIndex) {
		this.container = container;
		this.tagIndex = tagIndex;
		this.audienceIndex = audienceIndex;
	}

	// Nhóm 3: Phương thức dựng giao diện biểu đồ thanh ngang và bảng dữ liệu
	public render(): void {
		this.container.empty();

		const card = this.container.createDiv({
			cls: `content-compass-card ${this.isCollapsed ? "is-collapsed" : ""}`,
		});
		const header = card.createDiv({ cls: "content-compass-card-header" });
		const title = header.createDiv({ cls: "content-compass-card-title cc-collapsible-title" });
		const titleIcon = title.createSpan({ cls: "cc-icon" });
		title.createSpan({ text: "Tỷ trọng & Sức khỏe Trụ cột (Pillar Health)" });

		const cardBody = card.createDiv({ cls: "cc-card-collapsible-body" });
		if (this.isCollapsed) {
			cardBody.style.display = "none";
		}
		const syncCollapseTitle = () => {
			titleIcon.empty();
			setIcon(titleIcon, this.isCollapsed ? "chevron-right" : "chevron-down");
			title.setAttribute(
				"title",
				this.isCollapsed ? "Bấm để Hiện bảng" : "Bấm để Ẩn bảng"
			);
		};
		syncCollapseTitle();
		title.addEventListener("click", () => {
			this.isCollapsed = !this.isCollapsed;
			card.toggleClass("is-collapsed", this.isCollapsed);
			cardBody.style.display = this.isCollapsed ? "none" : "";
			syncCollapseTitle();
		});

		const pillars = this.tagIndex.getPillars();
		let totalTopics = 0;
		for (const p of pillars.values()) {
			totalTopics += p.topicIds.length;
		}

		if (pillars.size === 0 || totalTopics === 0) {
			const emptyMsg = cardBody.createDiv({ cls: "content-compass-placeholder" });
			emptyMsg.setText("Chưa có đủ dữ liệu topics để tính tỷ trọng Pillar.");
			return;
		}

		// 1. Danh sách biểu đồ thanh tiến trình
		const list = cardBody.createDiv({ cls: "content-compass-health-list" });

		let colorIdx = 0;
		const tableRows: Array<{ name: string; topics: number; audiences: number; percent: number; color: string }> = [];

		for (const [pillarName, pillarNode] of pillars.entries()) {
			const count = pillarNode.topicIds.length;
			const percent = totalTopics > 0 ? Math.round((count / totalTopics) * 100) : 0;
			const color = PILLAR_COLORS[colorIdx % PILLAR_COLORS.length];
			colorIdx++;

			tableRows.push({
				name: pillarName,
				topics: count,
				audiences: pillarNode.audienceSlugs.length,
				percent,
				color,
			});

			const item = list.createDiv({ cls: "content-compass-health-item" });
			const label = item.createDiv({ cls: "content-compass-health-label" });
			
			const nameSpan = label.createSpan({ text: pillarName });
			nameSpan.style.color = color;
			nameSpan.style.fontWeight = "600";

			label.createSpan({
				text: `${count} topics (${percent}%) • ${pillarNode.audienceSlugs.length} audiences`,
				cls: "content-compass-health-stats",
			});

			const track = item.createDiv({ cls: "content-compass-health-track" });
			const fill = track.createDiv({ cls: "content-compass-health-fill" });
			fill.style.width = `${percent}%`;
			fill.style.backgroundColor = color;
		}

		// 2. Bảng thống kê số liệu chi tiết
		const tableContainer = cardBody.createDiv({ cls: "content-compass-table-container" });
		const table = tableContainer.createEl("table", { cls: "content-compass-data-table" });

		// Header bảng
		const thead = table.createEl("thead");
		const headRow = thead.createEl("tr");
		headRow.createEl("th", { text: "Trụ cột Nội dung (Pillar)" });
		headRow.createEl("th", { text: "Topics" });
		headRow.createEl("th", { text: "Audiences" });
		headRow.createEl("th", { text: "Tỷ trọng" });

		// Body bảng
		const tbody = table.createEl("tbody");
		for (const row of tableRows) {
			const tr = tbody.createEl("tr");
			const nameTd = tr.createEl("td");
			const dot = nameTd.createSpan({ cls: "content-compass-color-dot" });
			dot.style.backgroundColor = row.color;
			nameTd.createSpan({ text: row.name });

			tr.createEl("td", { text: `${row.topics}` });
			tr.createEl("td", { text: `${row.audiences}` });
			tr.createEl("td", { text: `${row.percent}%` });
		}

		// Footer tổng kết
		const tfoot = table.createEl("tfoot");
		const footRow = tfoot.createEl("tr");
		footRow.createEl("td", { text: "Tổng cộng" });
		footRow.createEl("td", { text: `${totalTopics}` });
		footRow.createEl("td", { text: `${this.audienceIndex.getAudienceCount()}` });
		footRow.createEl("td", { text: "100%" });
	}
}
