/**
 * Tên file: DateRangePickerPopover.ts
 * Last update: 03/11/2026 15:22 (GMT+7)
 * Vai trò: Component nút chọn khoảng thời gian tích hợp Popover 3 cột chuẩn Apple / Analytics
 *          (Cột 1: Chọn nhanh Presets, Cột 2 & 3: Lịch kép 2 tháng cho phép chọn Từ ngày -> Đến ngày,
 *          Thanh dưới: Dropdown chọn đơn vị xem Ngày/Tuần/Tháng/Năm và Mốc thời gian).
 * Được sử dụng khi nào?: Được gắn vào thanh Header của TimelineChartView, TagRankingView và thanh lọc của Danh sách bài viết (ImportEngineView).
 * Output: Nút bấm gọn gàng hiển thị tóm tắt khoảng ngày + đơn vị xem, khi click mở Popover 3 cột tương tác.
 * Tóm tắt logic hoạt động: Quản lý trạng thái presetId, startDate, endDate, groupBy, dateBasis; tự động tính toán
 *          lưới lịch 2 tháng liền kề, cập nhật nhãn nút tại chỗ (in-place) và gọi callback onApply khi người dùng bấm Áp dụng.
 */

import { setIcon } from "obsidian";
import { TimelineGroupBy } from "../data/EngagementStore";

// Nhóm 1: Định nghĩa cấu trúc dữ liệu trạng thái Bộ chọn Thời gian
export type DatePresetId =
	| "today"
	| "yesterday"
	| "7d"
	| "30d"
	| "90d"
	| "this_week"
	| "this_month"
	| "last_month"
	| "this_year"
	| "all"
	| "custom";

export interface DateRangeSelection {
	presetId: DatePresetId;
	startDate: string; // YYYY-MM-DD (rỗng nếu là "all")
	endDate: string;   // YYYY-MM-DD (rỗng nếu là "all")
	groupBy?: TimelineGroupBy;
	dateBasis?: "published" | "collected";
}

interface PresetOption {
	id: DatePresetId;
	label: string;
}

const PRESET_OPTIONS: PresetOption[] = [
	{ id: "today", label: "Hôm nay" },
	{ id: "yesterday", label: "Hôm qua" },
	{ id: "7d", label: "7 ngày trước" },
	{ id: "30d", label: "30 ngày trước" },
	{ id: "90d", label: "90 ngày trước" },
	{ id: "this_week", label: "Tuần này" },
	{ id: "this_month", label: "Tháng này" },
	{ id: "last_month", label: "Tháng trước" },
	{ id: "this_year", label: "Năm nay" },
	{ id: "all", label: "Tất cả thời gian" },
	{ id: "custom", label: "Tùy chỉnh ngày..." },
];

const GROUP_BY_LABELS: Record<TimelineGroupBy, string> = {
	day: "Ngày",
	week: "Tuần",
	month: "Tháng",
	year: "Năm",
};

// Nhóm 2: Các hàm tiện ích xử lý định dạng ngày tháng YYYY-MM-DD và tính khoảng ngày theo Preset
function toYmd(d: Date): string {
	const y = d.getFullYear();
	const m = String(d.getMonth() + 1).padStart(2, "0");
	const day = String(d.getDate()).padStart(2, "0");
	return `${y}-${m}-${day}`;
}

function formatVnShort(ymd: string): string {
	if (!ymd) return "";
	const parts = ymd.split("-");
	if (parts.length !== 3) return ymd;
	return `${parts[2]}/${parts[1]}/${parts[0]}`;
}

export function computeRangeForPreset(presetId: DatePresetId): { startDate: string; endDate: string } {
	const now = new Date();
	const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());

	if (presetId === "all") {
		return { startDate: "", endDate: "" };
	}
	if (presetId === "today") {
		const s = toYmd(today);
		return { startDate: s, endDate: s };
	}
	if (presetId === "yesterday") {
		const yest = new Date(today.getTime() - 86400000);
		const s = toYmd(yest);
		return { startDate: s, endDate: s };
	}
	if (presetId === "7d") {
		const start = new Date(today.getTime() - 6 * 86400000);
		return { startDate: toYmd(start), endDate: toYmd(today) };
	}
	if (presetId === "30d") {
		const start = new Date(today.getTime() - 29 * 86400000);
		return { startDate: toYmd(start), endDate: toYmd(today) };
	}
	if (presetId === "90d") {
		const start = new Date(today.getTime() - 89 * 86400000);
		return { startDate: toYmd(start), endDate: toYmd(today) };
	}
	if (presetId === "this_week") {
		const dayOfWeek = today.getDay() || 7; // Thứ 2 = 1 ... Chủ nhật = 7
		const monday = new Date(today.getTime() - (dayOfWeek - 1) * 86400000);
		return { startDate: toYmd(monday), endDate: toYmd(today) };
	}
	if (presetId === "this_month") {
		const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
		return { startDate: toYmd(firstDay), endDate: toYmd(today) };
	}
	if (presetId === "last_month") {
		const firstPrev = new Date(today.getFullYear(), today.getMonth() - 1, 1);
		const lastPrev = new Date(today.getFullYear(), today.getMonth(), 0);
		return { startDate: toYmd(firstPrev), endDate: toYmd(lastPrev) };
	}
	if (presetId === "this_year") {
		const firstJan = new Date(today.getFullYear(), 0, 1);
		return { startDate: toYmd(firstJan), endDate: toYmd(today) };
	}
	// Mặc định 30 ngày nếu chuyển sang custom mà chưa có ngày
	const fallbackStart = new Date(today.getTime() - 29 * 86400000);
	return { startDate: toYmd(fallbackStart), endDate: toYmd(today) };
}

// Nhóm 3: Hàm khởi tạo Cụm điều khiển Thời gian tích hợp (Nút mở Lịch 3 Cột + Dropbox Gộp dữ liệu Ngày/Tuần/Tháng/Năm)
export function renderDateRangePickerButton(
	parentEl: HTMLElement,
	current: DateRangeSelection,
	options: {
		showGroupBy: boolean;
		showDateBasis: boolean;
	},
	onApply: (next: DateRangeSelection) => void
): HTMLElement {
	const wrapper = parentEl.createDiv({ cls: "cc-daterange-wrapper" });
	let activeSelection: DateRangeSelection = { ...current };

	// Cụm điều khiển liền khối: [ Nút chọn khoảng ngày ▾ | Dropbox Gộp theo: Ngày/Tuần/Tháng/Năm ]
	const controlBar = wrapper.createDiv({ cls: "cc-daterange-bar" });

	const formatRangeText = (sel: DateRangeSelection): string => {
		const presetObj = PRESET_OPTIONS.find((p) => p.id === sel.presetId);
		const presetLabel = presetObj ? presetObj.label : "Tùy chỉnh";
		if (sel.presetId === "custom" && sel.startDate && sel.endDate) {
			return `${formatVnShort(sel.startDate)} → ${formatVnShort(sel.endDate)}`;
		}
		if (sel.startDate && sel.endDate) {
			return `${presetLabel} (${formatVnShort(sel.startDate).slice(0, 5)} – ${formatVnShort(sel.endDate).slice(0, 5)})`;
		}
		return presetLabel;
	};

	const triggerBtn = controlBar.createEl("button", {
		cls: "content-compass-refresh-btn cc-daterange-trigger",
		attr: { type: "button" },
	});
	triggerBtn.setAttribute("title", "Bấm để mở bảng chọn khoảng thời gian 3 cột (Chọn nhanh + Lịch kép)");
	const calIcon = triggerBtn.createSpan({ cls: "cc-icon" });
	setIcon(calIcon, "calendar");
	const labelSpan = triggerBtn.createSpan({ text: formatRangeText(activeSelection) });
	const chevIcon = triggerBtn.createSpan({ cls: "cc-icon" });
	setIcon(chevIcon, "chevron-down");

	// Dropbox Gộp dữ liệu theo Thời gian (Ngày / Tuần / Tháng / Năm) tích hợp ngay cạnh nút chọn lịch
	let inlineGroupSelect: HTMLSelectElement | null = null;
	if (options.showGroupBy) {
		const inlineGroupWrap = controlBar.createDiv({ cls: "cc-inline-group-wrap" });
		inlineGroupSelect = inlineGroupWrap.createEl("select", {
			cls: "cc-inline-group-select",
		}) as HTMLSelectElement;
		inlineGroupSelect.setAttribute("title", "Chọn đơn vị gộp dữ liệu theo thời gian (Ngày, Tuần, Tháng, Năm)");
		inlineGroupSelect.createEl("option", { value: "day", text: "Xem theo: Ngày" });
		inlineGroupSelect.createEl("option", { value: "week", text: "Xem theo: Tuần" });
		inlineGroupSelect.createEl("option", { value: "month", text: "Xem theo: Tháng" });
		inlineGroupSelect.createEl("option", { value: "year", text: "Xem theo: Năm" });
		inlineGroupSelect.value = activeSelection.groupBy || "day";
		inlineGroupSelect.addEventListener("change", (e) => {
			e.stopPropagation();
			if (!inlineGroupSelect) return;
			activeSelection = {
				...activeSelection,
				groupBy: inlineGroupSelect.value as TimelineGroupBy,
			};
			draftGroupBy = activeSelection.groupBy || "day";
			onApply(activeSelection);
		});
	}

	// Khung Popover 3 cột thu gọn chuẩn Apple (Mặc định ẩn)
	const popover = wrapper.createDiv({ cls: "cc-daterange-popover" });
	popover.style.display = "none";

	// Bản sao trạng thái tạm thời khi người dùng đang thao tác trong Popover
	let draftPreset: DatePresetId = activeSelection.presetId;
	let draftStart: string = activeSelection.startDate;
	let draftEnd: string = activeSelection.endDate;
	let draftGroupBy: TimelineGroupBy = activeSelection.groupBy || "day";
	let draftBasis: "published" | "collected" = activeSelection.dateBasis || "published";
	let pickingPhase: "start" | "end" = "start";

	// Tháng gốc của Cột lịch bên phải (Mặc định là tháng hiện tại)
	const now = new Date();
	let rightCalYear = now.getFullYear();
	let rightCalMonth = now.getMonth(); // 0..11

	// Nhóm 4: Hàm vẽ lại nội dung bên trong Popover 3 cột thu gọn
	const rebuildPopoverContent = () => {
		popover.empty();

		// 1. Thanh cấu hình gọn phía trên Popover: Từ ngày -> Đến ngày + Dropbox Gộp theo + Dropbox Mốc thời gian
		const topBar = popover.createDiv({ cls: "cc-daterange-top-bar" });

		const rangeInputs = topBar.createDiv({ cls: "cc-daterange-inputs" });
		rangeInputs.createSpan({ text: "Từ", cls: "cc-daterange-lbl" });
		const inpStart = rangeInputs.createEl("input", {
			type: "date",
			cls: "cc-daterange-date-input",
			value: draftStart,
		}) as HTMLInputElement;
		inpStart.addEventListener("change", () => {
			if (inpStart.value) {
				draftPreset = "custom";
				draftStart = inpStart.value;
				if (draftEnd && draftStart > draftEnd) {
					draftEnd = draftStart;
				}
				rebuildPopoverContent();
			}
		});

		rangeInputs.createSpan({ text: "→", cls: "cc-daterange-lbl" });
		const inpEnd = rangeInputs.createEl("input", {
			type: "date",
			cls: "cc-daterange-date-input",
			value: draftEnd,
		}) as HTMLInputElement;
		inpEnd.addEventListener("change", () => {
			if (inpEnd.value) {
				draftPreset = "custom";
				draftEnd = inpEnd.value;
				if (draftStart && draftEnd < draftStart) {
					draftStart = draftEnd;
				}
				rebuildPopoverContent();
			}
		});

		// Dropbox "Gộp theo: Ngày / Tuần / Tháng / Năm" ngay trên thanh đầu Popover
		if (options.showGroupBy) {
			const grpWrap = topBar.createDiv({ cls: "cc-daterange-inputs" });
			grpWrap.createSpan({ text: "Gộp:", cls: "cc-daterange-lbl" });
			const selGroup = grpWrap.createEl("select", { cls: "cc-daterange-select" }) as HTMLSelectElement;
			selGroup.createEl("option", { value: "day", text: "Theo Ngày" });
			selGroup.createEl("option", { value: "week", text: "Theo Tuần" });
			selGroup.createEl("option", { value: "month", text: "Theo Tháng" });
			selGroup.createEl("option", { value: "year", text: "Theo Năm" });
			selGroup.value = draftGroupBy;
			selGroup.addEventListener("change", () => {
				draftGroupBy = selGroup.value as TimelineGroupBy;
			});
		}

		// Dropbox "Mốc thời gian: Ngày đăng / Lúc quét"
		if (options.showDateBasis) {
			const basisWrap = topBar.createDiv({ cls: "cc-daterange-inputs" });
			basisWrap.createSpan({ text: "Mốc:", cls: "cc-daterange-lbl" });
			const selBasis = basisWrap.createEl("select", { cls: "cc-daterange-select" }) as HTMLSelectElement;
			selBasis.createEl("option", { value: "published", text: "Ngày đăng bài" });
			selBasis.createEl("option", { value: "collected", text: "Thời điểm quét" });
			selBasis.value = draftBasis;
			selBasis.addEventListener("change", () => {
				draftBasis = selBasis.value as "published" | "collected";
			});
		}

		// 2. Khối chính 3 cột thu gọn: [Cột 1: Chọn nhanh] | [Cột 2: Lịch Tháng trước] | [Cột 3: Lịch Tháng này]
		const threeCols = popover.createDiv({ cls: "cc-daterange-columns" });

		// --- CỘT 1: Danh sách Chọn nhanh (Presets Sidebar) ---
		const colPresets = threeCols.createDiv({ cls: "cc-daterange-presets" });
		for (const p of PRESET_OPTIONS) {
			const itemBtn = colPresets.createEl("button", {
				cls: `cc-preset-item ${draftPreset === p.id ? "is-active" : ""}`,
				text: p.label,
			});
			itemBtn.addEventListener("click", (e) => {
				e.stopPropagation();
				draftPreset = p.id;
				if (p.id !== "custom") {
					const computed = computeRangeForPreset(p.id);
					draftStart = computed.startDate;
					draftEnd = computed.endDate;
					if (draftEnd) {
						const endObj = new Date(draftEnd + "T00:00:00");
						if (!isNaN(endObj.getTime())) {
							rightCalYear = endObj.getFullYear();
							rightCalMonth = endObj.getMonth();
						}
					}
				}
				rebuildPopoverContent();
			});
		}

		// --- CỘT 2 & CỘT 3: Hai bảng lịch tháng liền kề (Dual Calendar) ---
		const leftDate = new Date(rightCalYear, rightCalMonth - 1, 1);
		const rightDate = new Date(rightCalYear, rightCalMonth, 1);

		renderMonthCalendar(threeCols, leftDate.getFullYear(), leftDate.getMonth(), "left");
		renderMonthCalendar(threeCols, rightDate.getFullYear(), rightDate.getMonth(), "right");

		// 3. Thanh Footer 1 dòng: Tóm tắt bên trái + Nút Hủy / Áp dụng bên phải
		const footer = popover.createDiv({ cls: "cc-daterange-footer" });
		const summaryText =
			draftPreset === "all"
				? "Phạm vi: Tất cả thời gian"
				: draftStart && draftEnd
				? `Đang chọn: ${formatVnShort(draftStart)} → ${formatVnShort(draftEnd)}`
				: "Chọn ngày bắt đầu và kết thúc trên lịch";
		footer.createSpan({ cls: "cc-daterange-summary", text: summaryText });

		const footerBtns = footer.createDiv({ cls: "cc-daterange-footer-btns" });
		const btnCancel = footerBtns.createEl("button", {
			cls: "content-compass-refresh-btn cc-btn-sm",
			text: "Hủy",
		});
		btnCancel.addEventListener("click", (e) => {
			e.stopPropagation();
			popover.style.display = "none";
		});

		const btnApply = footerBtns.createEl("button", {
			cls: "content-compass-import-btn cc-btn-sm",
			text: "Áp dụng",
			attr: { type: "button" },
		});
		btnApply.addEventListener("click", (e) => {
			e.stopPropagation();
			popover.style.display = "none";
			activeSelection = {
				presetId: draftPreset,
				startDate: draftStart,
				endDate: draftEnd,
				groupBy: draftGroupBy,
				dateBasis: draftBasis,
			};
			labelSpan.setText(formatRangeText(activeSelection));
			if (inlineGroupSelect && activeSelection.groupBy) {
				inlineGroupSelect.value = activeSelection.groupBy;
			}
			onApply(activeSelection);
		});
	};

	// Nhóm 5: Hàm dựng 1 cột lịch tháng (Tháng trước hoặc Tháng hiện tại)
	const renderMonthCalendar = (
		container: HTMLElement,
		year: number,
		month: number,
		side: "left" | "right"
	) => {
		const calCol = container.createDiv({ cls: "cc-daterange-calendar" });

		// Header điều hướng tháng (< Tháng X / 2026 >)
		const navHeader = calCol.createDiv({ cls: "cc-cal-header" });
		if (side === "left") {
			const prevBtn = navHeader.createEl("button", { cls: "content-compass-icon-btn" });
			const ic = prevBtn.createSpan({ cls: "cc-icon" });
			setIcon(ic, "chevron-left");
			prevBtn.addEventListener("click", (e) => {
				e.stopPropagation();
				rightCalMonth -= 1;
				if (rightCalMonth < 0) {
					rightCalMonth = 11;
					rightCalYear -= 1;
				}
				rebuildPopoverContent();
			});
		} else {
			navHeader.createSpan({ cls: "cc-cal-spacer" });
		}

		navHeader.createSpan({
			cls: "cc-cal-title",
			text: `Tháng ${month + 1} / ${year}`,
		});

		if (side === "right") {
			const nextBtn = navHeader.createEl("button", { cls: "content-compass-icon-btn" });
			const ic = nextBtn.createSpan({ cls: "cc-icon" });
			setIcon(ic, "chevron-right");
			nextBtn.addEventListener("click", (e) => {
				e.stopPropagation();
				rightCalMonth += 1;
				if (rightCalMonth > 11) {
					rightCalMonth = 0;
					rightCalYear += 1;
				}
				rebuildPopoverContent();
			});
		} else {
			navHeader.createSpan({ cls: "cc-cal-spacer" });
		}

		// Hàng tên các thứ trong tuần (T2 -> CN)
		const weekdaysGrid = calCol.createDiv({ cls: "cc-cal-weekdays" });
		for (const wd of ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]) {
			weekdaysGrid.createSpan({ text: wd });
		}

		// Lưới các ngày trong tháng
		const daysGrid = calCol.createDiv({ cls: "cc-cal-days" });
		const firstDay = new Date(year, month, 1);
		const startOffset = (firstDay.getDay() + 6) % 7; // Đổi sang Thứ 2 = 0 ... Chủ nhật = 6
		const daysInMonth = new Date(year, month + 1, 0).getDate();

		// Các ô trống đầu tháng
		for (let i = 0; i < startOffset; i++) {
			daysGrid.createSpan({ cls: "cc-cal-day is-empty" });
		}

		// Các ngày thực tế trong tháng
		for (let d = 1; d <= daysInMonth; d++) {
			const ymd = toYmd(new Date(year, month, d));
			const isStart = Boolean(draftStart && ymd === draftStart);
			const isEnd = Boolean(draftEnd && ymd === draftEnd);
			const isInRange = Boolean(draftStart && draftEnd && ymd > draftStart && ymd < draftEnd);

			const dayBtn = daysGrid.createEl("button", {
				cls: [
					"cc-cal-day",
					isStart ? "is-start" : "",
					isEnd ? "is-end" : "",
					isInRange ? "is-in-range" : "",
				]
					.filter(Boolean)
					.join(" "),
				text: String(d),
			});

			dayBtn.addEventListener("click", (e) => {
				e.stopPropagation();
				draftPreset = "custom";
				if (pickingPhase === "start" || !draftStart || (draftStart && draftEnd && draftStart !== draftEnd)) {
					draftStart = ymd;
					draftEnd = ymd;
					pickingPhase = "end";
				} else {
					if (ymd < draftStart) {
						draftEnd = draftStart;
						draftStart = ymd;
					} else {
						draftEnd = ymd;
					}
					pickingPhase = "start";
				}
				rebuildPopoverContent();
			});
		}
	};

	// Nhóm 6: Sự kiện đóng/mở Popover, căn vị trí thông minh không tràn màn hình và click ra ngoài để đóng
	triggerBtn.addEventListener("click", (e) => {
		e.stopPropagation();
		const isHidden = popover.style.display === "none";
		if (isHidden) {
			draftPreset = activeSelection.presetId;
			draftStart = activeSelection.startDate;
			draftEnd = activeSelection.endDate;
			draftGroupBy = activeSelection.groupBy || "day";
			draftBasis = activeSelection.dateBasis || "published";
			rebuildPopoverContent();

			const btnRect = triggerBtn.getBoundingClientRect();
			const popoverWidth = 520;
			if (btnRect.left + popoverWidth <= window.innerWidth - 20) {
				popover.style.left = "0";
				popover.style.right = "auto";
			} else {
				popover.style.right = "0";
				popover.style.left = "auto";
			}

			popover.style.display = "flex";
		} else {
			popover.style.display = "none";
		}
	});

	(wrapper as any).syncSelection = (next: DateRangeSelection) => {
		activeSelection = { ...next };
		labelSpan.setText(formatRangeText(activeSelection));
		if (inlineGroupSelect && activeSelection.groupBy) {
			inlineGroupSelect.value = activeSelection.groupBy;
		}
	};

	document.addEventListener("mousedown", (evt) => {
		if (popover.style.display !== "none" && !wrapper.contains(evt.target as Node)) {
			popover.style.display = "none";
		}
	});

	return wrapper;
}

