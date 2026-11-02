/**
 * Tên file: HierarchyBrowserView.ts
 * Last update: 23/10/2026 20:10 (GMT+7)
 * Vai trò: Renderer cho cây phả hệ Audience có thể thu gọn/mở rộng (collapsible tree).
 * Được sử dụng khi nào?: Trong tab Strategy để duyệt cấu trúc phân cấp Big/Little/Micro Job.
 * Output: Cây phả hệ tương tác với nút thu gọn/mở rộng, bộ lọc tìm kiếm tức thời và highlight Buyer Job.
 * Tóm tắt logic hoạt động: Duyệt đệ quy từ các root node của AudienceIndex, tạo phần tử DOM
 * hỗ trợ toggle đóng/mở chi nhánh, tìm kiếm theo tên và nhấp để mở ghi chú trong vault.
 */

import { App, setIcon } from "obsidian";
import { AudienceIndex, AudienceNode } from "../data/AudienceIndex";

// Nhóm 1: Lớp hiển thị cây phân cấp HierarchyBrowserView chuẩn macOS Finder Outline
export class HierarchyBrowserView {
	private container: HTMLElement;
	private audienceIndex: AudienceIndex;
	private app: App;
	private searchQuery: string = "";
	private onlyBuyerJobs: boolean = false;

	constructor(container: HTMLElement, audienceIndex: AudienceIndex, app: App) {
		this.container = container;
		this.audienceIndex = audienceIndex;
		this.app = app;
	}

	// Nhóm 2: Phương thức dựng giao diện cây phả hệ kèm thanh công cụ lọc
	public render(): void {
		this.container.empty();

		const card = this.container.createDiv({ cls: "content-compass-card" });
		
		// Header tiêu đề và thống kê
		const header = card.createDiv({ cls: "content-compass-card-header" });
		const title = header.createDiv({ cls: "content-compass-card-title" });
		const titleIcon = title.createSpan({ cls: "cc-icon" });
		setIcon(titleIcon, "git-branch");
		title.createSpan({ text: "Cây Phả hệ Khán giả (Audience Hierarchy)" });

		const buyerCount = this.audienceIndex.getBuyerJobCount();
		const totalCount = this.audienceIndex.getAudienceCount();
		const subtitle = header.createDiv({ cls: "content-compass-treemap-badge" });
		subtitle.setText(`${totalCount} Audiences • ${buyerCount} Buyer Jobs`);

		// Thanh công cụ: Tìm kiếm (với Icon Vector) và Công tắc UISwitch
		const toolbar = card.createDiv({ cls: "content-compass-tree-toolbar" });
		
		const searchBox = toolbar.createDiv({ cls: "content-compass-search-box" });
		const searchIcon = searchBox.createSpan({ cls: "cc-icon" });
		setIcon(searchIcon, "search");
		const searchInput = searchBox.createEl("input", {
			type: "text",
			cls: "content-compass-search-input",
			placeholder: "Tìm kiếm audience...",
		});
		searchInput.value = this.searchQuery;
		searchInput.addEventListener("input", () => {
			this.searchQuery = searchInput.value.trim().toLowerCase();
			this.renderTree(treeContainer);
		});

		const buyerFilterLabel = toolbar.createEl("label", { cls: "content-compass-filter-label" });
		const buyerCheckbox = buyerFilterLabel.createEl("input", {
			type: "checkbox",
			cls: "content-compass-switch",
		});
		buyerCheckbox.checked = this.onlyBuyerJobs;
		buyerFilterLabel.createSpan({ text: "Chỉ Buyer Jobs" });
		buyerCheckbox.addEventListener("change", () => {
			this.onlyBuyerJobs = buyerCheckbox.checked;
			this.renderTree(treeContainer);
		});

		const treeContainer = card.createDiv({ cls: "content-compass-hierarchy" });
		this.renderTree(treeContainer);
	}

	// Nhóm 3: Dựng danh sách cây phả hệ
	private renderTree(treeContainer: HTMLElement): void {
		treeContainer.empty();

		const rootNodes = this.audienceIndex.getRootNodes();
		if (rootNodes.length === 0) {
			const emptyMsg = treeContainer.createDiv({ cls: "content-compass-placeholder" });
			emptyMsg.setText("Chưa tìm thấy file Audience nào trong vault.");
			return;
		}

		const rootList = treeContainer.createEl("ul", { cls: "content-compass-tree-list" });
		let renderedAny = false;

		for (const root of rootNodes) {
			if (this.nodeMatchesFilter(root)) {
				this.renderNode(root, rootList);
				renderedAny = true;
			}
		}

		if (!renderedAny) {
			const emptyMsg = treeContainer.createDiv({ cls: "content-compass-placeholder" });
			emptyMsg.setText("Không có Audience nào khớp với bộ lọc.");
		}
	}

	// Nhóm 4: Kiểm tra điều kiện tìm kiếm và lọc Buyer Job
	private nodeMatchesFilter(node: AudienceNode): boolean {
		if (this.onlyBuyerJobs && !node.isBuyerJob) {
			// Kiểm tra xem có con nào là buyer job không
			const descendants = this.audienceIndex.getDescendants(node.slug);
			const hasBuyerDescendant = descendants.some(d => d.isBuyerJob);
			if (!hasBuyerDescendant) return false;
		}

		if (this.searchQuery.length > 0) {
			const textMatch = node.displayName.toLowerCase().includes(this.searchQuery) ||
				node.slug.toLowerCase().includes(this.searchQuery);
			if (textMatch) return true;

			// Kiểm tra con cháu xem có khớp query không
			const descendants = this.audienceIndex.getDescendants(node.slug);
			return descendants.some(d =>
				d.displayName.toLowerCase().includes(this.searchQuery) ||
				d.slug.toLowerCase().includes(this.searchQuery)
			);
		}

		return true;
	}

	// Nhóm 5: Hàm dựng đệ quy từng nút cây với nút đóng/mở (collapsible)
	private renderNode(node: AudienceNode, parentListEl: HTMLElement): void {
		const li = parentListEl.createEl("li", { cls: "content-compass-tree-item" });
		const nodeRow = li.createDiv({ cls: `content-compass-tree-node ${node.isBuyerJob ? "is-buyer-node" : ""}` });

		const hasChildren = node.childSlugs.length > 0;
		let isExpanded = true;

		// Nút thu gọn / mở rộng (Vector Chevron xoay 90deg chuẩn macOS Finder)
		const toggleBtn = nodeRow.createSpan({
			cls: `content-compass-tree-toggle ${hasChildren ? "is-expanded" : ""}`,
		});
		if (hasChildren) {
			setIcon(toggleBtn, "chevron-right");
			toggleBtn.addEventListener("click", (e) => {
				e.stopPropagation();
				isExpanded = !isExpanded;
				toggleBtn.toggleClass("is-expanded", isExpanded);
				if (subList) {
					subList.style.display = isExpanded ? "block" : "none";
				}
			});
		}

		// Chấm tròn màu hệ thống Apple theo cấp bậc JTBD (Big / Little / Micro)
		const dotClass =
			node.level === "big" ? "is-big" : node.level === "little" ? "is-little" : "is-micro";
		const iconSpan = nodeRow.createSpan({ cls: `content-compass-level-dot ${dotClass}` });
		iconSpan.setAttribute("title", `Cấp bậc: ${node.level.toUpperCase()} Job`);

		// Tên Audience (Clickable để mở note trong Obsidian)
		const labelSpan = nodeRow.createSpan({ cls: "content-compass-node-label", text: node.displayName });
		nodeRow.addEventListener("click", () => {
			this.app.workspace.openLinkText(node.slug, "");
		});

		// Badge Buyer Job
		if (node.isBuyerJob) {
			const badge = nodeRow.createSpan({ cls: "content-compass-badge-buyer", text: "BUYER" });
			badge.setAttribute("title", "Khách hàng mục tiêu gắn liền quyết định mua hàng");
		}

		// Hiển thị số bước tiến trình tiếp theo (next_job_step)
		if (node.nextJobStepSlugs.length > 0) {
			const stepBadge = nodeRow.createSpan({ cls: "content-compass-step-badge" });
			stepBadge.setText(`→ [${node.nextJobStepSlugs.length} steps]`);
			stepBadge.setAttribute(
				"title",
				`Tiến trình tiếp theo:\n${node.nextJobStepSlugs.join("\n")}`
			);
		}

		// Nhánh con đệ quy
		let subList: HTMLElement | null = null;
		if (hasChildren) {
			subList = li.createEl("ul", { cls: "content-compass-tree-list" });
			for (const childSlug of node.childSlugs) {
				const childNode = this.audienceIndex.getNode(childSlug);
				if (childNode && this.nodeMatchesFilter(childNode)) {
					this.renderNode(childNode, subList);
				}
			}
		}
	}
}
