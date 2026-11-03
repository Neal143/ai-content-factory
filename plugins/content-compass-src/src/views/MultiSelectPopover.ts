/**
 * Ten file: MultiSelectPopover.ts
 * Last update: 03/11/2026 12:15 (GMT+7)
 * Vai tro: Component Popover chon nhieu muc (Multi-Select Checkbox Popover) chuan Apple HIG.
 * Duoc su dung khi nao?: Khi nguoi dung loc nhieu Chi so, nhieu Nguon/Trang hoac nhieu Audience tren TimelineChartView va TagRankingView.
 * Output: Nut bam hien thi nhan tom tat thong minh + Popover chua o tim kiem, nut Chon tat ca / Bo chon va danh sach Checkbox kem cham mau.
 * Tom tat logic hoat dong: Quan ly trang thai mang gia tri duoc chon, giu Popover luon mo khi tich chon nhieu muc lien tiep va cap nhat bieu do tuc thoi (in-place) ngay sau moi thao tac tich chon.
 */

import { setIcon } from "obsidian";

// Nhom 1: Interface cau hinh cho tung muc chon va toan bo Popover
export interface MultiSelectOption {
	value: string;
	label: string;
	group?: string;
	color?: string;
	sublabel?: string;
}

export interface MultiSelectConfig {
	prefixLabel: string;
	allLabel?: string;
	options: MultiSelectOption[];
	selectedValues: string[];
	allWhenEmpty?: boolean; // true: mang [] mang y nghia la "Tat ca"
	minSelected?: number; // VD: 1 doi voi bo chon Chi so (luon giu it nhat 1 duong tren do thi)
	enableSearch?: boolean;
	widthPx?: number;
}

// Nhom 2: Ham tien ich tinh nhan tom tat tren nut bam
function formatTriggerSummary(cfg: MultiSelectConfig): string {
	const sel = cfg.selectedValues;
	const total = cfg.options.length;
	const allText = cfg.allLabel || "Tất cả";

	if (cfg.allWhenEmpty && (sel.length === 0 || sel.length === total)) {
		return `${cfg.prefixLabel}: ${allText}`;
	}
	if (sel.length === 0) {
		return `${cfg.prefixLabel}: ${allText}`;
	}

	const selectedLabels = sel
		.map((v) => cfg.options.find((o) => o.value === v)?.label || v)
		.filter(Boolean);

	if (selectedLabels.length === 1) {
		const lbl = selectedLabels[0];
		return `${cfg.prefixLabel}: ${lbl.length > 22 ? lbl.slice(0, 20) + "…" : lbl}`;
	}
	if (selectedLabels.length === 2) {
		const first = selectedLabels[0].length > 14 ? selectedLabels[0].slice(0, 12) + "…" : selectedLabels[0];
		const second = selectedLabels[1].length > 14 ? selectedLabels[1].slice(0, 12) + "…" : selectedLabels[1];
		return `${cfg.prefixLabel}: ${first}, ${second}`;
	}
	return `${cfg.prefixLabel}: ${selectedLabels.length} mục đã chọn`;
}

// Nhom 3: Ham chinh render nut Trigger va Popover Multi-select
export function renderMultiSelectPopoverButton(
	parent: HTMLElement,
	config: MultiSelectConfig,
	onChange: (nextValues: string[]) => void
): HTMLElement {
	const wrapper = parent.createDiv({ cls: "cc-multiselect-wrapper" });

	const triggerBtn = wrapper.createEl("button", {
		cls: "content-compass-secondary-btn cc-multiselect-trigger",
		attr: { type: "button" },
	});

	const hasActiveFilter = config.allWhenEmpty
		? config.selectedValues.length > 0 && config.selectedValues.length < config.options.length
		: config.selectedValues.length > 1;
	if (hasActiveFilter) {
		triggerBtn.addClass("is-filtered");
	}

	const textSpan = triggerBtn.createSpan({
		cls: "cc-multiselect-trigger-text",
		text: formatTriggerSummary(config),
	});
	const chevSpan = triggerBtn.createSpan({ cls: "cc-icon" });
	setIcon(chevSpan, "chevron-down");

	let popoverEl: HTMLElement | null = null;
	let workingValues: string[] = [...config.selectedValues];
	let searchQuery = "";

	const closePopover = () => {
		if (popoverEl) {
			popoverEl.remove();
			popoverEl = null;
		}
		document.removeEventListener("mousedown", onOutsideClick, true);
	};

	const onOutsideClick = (ev: MouseEvent) => {
		if (!wrapper.isConnected) {
			closePopover();
			return;
		}
		const target = ev.target as Node | null;
		if (target && !wrapper.contains(target)) {
			closePopover();
		}
	};

	const notifyChange = (nextVals: string[]) => {
		workingValues = [...nextVals];
		config.selectedValues = [...nextVals];
		textSpan.setText(formatTriggerSummary(config));
		const activeNow = config.allWhenEmpty
			? nextVals.length > 0 && nextVals.length < config.options.length
			: nextVals.length > 1;
		triggerBtn.toggleClass("is-filtered", activeNow);
		onChange([...nextVals]);
	};

	const renderPopoverContent = () => {
		if (!popoverEl) return;
		popoverEl.empty();

		// 1. O tim kiem nhanh (neu bat hoac danh sach >= 5 muc)
		if (config.enableSearch !== false && config.options.length >= 5) {
			const searchWrap = popoverEl.createDiv({ cls: "cc-multiselect-search-wrap" });
			const searchInput = searchWrap.createEl("input", {
				cls: "cc-multiselect-search-input",
				attr: {
					type: "text",
					placeholder: `Tìm ${config.prefixLabel.toLowerCase()}...`,
				},
			}) as HTMLInputElement;
			searchInput.value = searchQuery;
			searchInput.addEventListener("input", () => {
				searchQuery = searchInput.value;
				renderListItems(listContainer, statusLbl);
			});
			setTimeout(() => searchInput.focus(), 10);
		}

		// 2. Thanh cong cu nhanh: Chon tat ca / Bo chon (Dat lai)
		const actionRow = popoverEl.createDiv({ cls: "cc-multiselect-actions" });
		const statusLbl = actionRow.createSpan({
			cls: "cc-multiselect-count",
			text:
				config.allWhenEmpty && workingValues.length === 0
					? `Đang lấy tất cả (${config.options.length})`
					: `Đã chọn ${workingValues.length}/${config.options.length}`,
		});

		const updateStatusText = () => {
			statusLbl.setText(
				config.allWhenEmpty && workingValues.length === 0
					? `Đang lấy tất cả (${config.options.length})`
					: `Đã chọn ${workingValues.length}/${config.options.length}`
			);
		};

		const btnGroup = actionRow.createDiv({ cls: "cc-multiselect-action-btns" });
		const selectAllBtn = btnGroup.createEl("button", {
			cls: "cc-multiselect-link-btn",
			text: "Chọn tất cả",
			attr: { type: "button" },
		});
		selectAllBtn.addEventListener("click", (e) => {
			e.stopPropagation();
			const allVals = config.options.map((o) => o.value);
			notifyChange(allVals);
			updateStatusText();
			renderListItems(listContainer, statusLbl);
		});

		const clearBtn = btnGroup.createEl("button", {
			cls: "cc-multiselect-link-btn",
			text: config.allWhenEmpty ? "Mặc định (Tất cả)" : "Đặt lại",
			attr: { type: "button" },
		});
		clearBtn.addEventListener("click", (e) => {
			e.stopPropagation();
			if (config.allWhenEmpty) {
				notifyChange([]);
			} else {
				const fallback = config.options.length > 0 ? [config.options[0].value] : [];
				notifyChange(fallback);
			}
			updateStatusText();
			renderListItems(listContainer, statusLbl);
		});

		// 3. Danh sach Checkbox
		const listContainer = popoverEl.createDiv({ cls: "cc-multiselect-list" });
		renderListItems(listContainer, statusLbl);
	};

	const renderListItems = (listContainer: HTMLElement, statusLbl?: HTMLElement) => {
		listContainer.empty();
		const q = searchQuery.trim().toLowerCase();
		const filtered = config.options.filter(
			(o) =>
				!q ||
				o.label.toLowerCase().includes(q) ||
				(o.sublabel && o.sublabel.toLowerCase().includes(q)) ||
				(o.group && o.group.toLowerCase().includes(q))
		);

		if (filtered.length === 0) {
			listContainer.createDiv({
				cls: "cc-multiselect-empty",
				text: "Không có mục nào khớp từ khóa",
			});
			return;
		}

		let currentGroup = "";
		for (const opt of filtered) {
			if (opt.group && opt.group !== currentGroup) {
				currentGroup = opt.group;
				listContainer.createDiv({
					cls: "cc-multiselect-group-header",
					text: currentGroup,
				});
			}

			const isChecked = workingValues.includes(opt.value);
			const row = listContainer.createEl("label", {
				cls: `cc-multiselect-item ${isChecked ? "is-checked" : ""}`,
			});

			const cb = row.createEl("input", {
				attr: { type: "checkbox" },
			}) as HTMLInputElement;
			cb.checked = isChecked;

			if (opt.color) {
				const dot = row.createSpan({ cls: "cc-multiselect-dot" });
				dot.style.backgroundColor = opt.color;
			}

			const lblWrap = row.createDiv({ cls: "cc-multiselect-item-labels" });
			lblWrap.createSpan({ cls: "cc-multiselect-item-text", text: opt.label });
			if (opt.sublabel) {
				lblWrap.createSpan({ cls: "cc-multiselect-item-sub", text: opt.sublabel });
			}

			cb.addEventListener("change", () => {
				let next: string[];
				if (cb.checked) {
					next = workingValues.includes(opt.value)
						? [...workingValues]
						: [...workingValues, opt.value];
				} else {
					next = workingValues.filter((v) => v !== opt.value);
					const minReq = config.minSelected || 0;
					if (next.length < minReq) {
						cb.checked = true;
						return;
					}
				}
				row.toggleClass("is-checked", cb.checked);
				notifyChange(next);
				if (statusLbl) {
					statusLbl.setText(
						config.allWhenEmpty && workingValues.length === 0
							? `Đang lấy tất cả (${config.options.length})`
							: `Đã chọn ${workingValues.length}/${config.options.length}`
					);
				}
			});
		}
	};

	triggerBtn.addEventListener("click", (ev) => {
		ev.stopPropagation();
		if (popoverEl) {
			closePopover();
			return;
		}
		workingValues = [...config.selectedValues];
		searchQuery = "";
		popoverEl = wrapper.createDiv({ cls: "cc-multiselect-popover" });
		popoverEl.addEventListener("mousedown", (e) => e.stopPropagation());
		popoverEl.addEventListener("click", (e) => e.stopPropagation());
		if (config.widthPx) {
			popoverEl.style.width = `${config.widthPx}px`;
		}
		renderPopoverContent();
		document.addEventListener("mousedown", onOutsideClick, true);
	});

	(wrapper as any).syncSelectedValues = (nextVals: string[]) => {
		workingValues = [...nextVals];
		config.selectedValues = [...nextVals];
		textSpan.setText(formatTriggerSummary(config));
		const activeNow = config.allWhenEmpty
			? nextVals.length > 0 && nextVals.length < config.options.length
			: nextVals.length > 1;
		triggerBtn.toggleClass("is-filtered", activeNow);
		if (popoverEl) {
			renderPopoverContent();
		}
	};

	return wrapper;
}

