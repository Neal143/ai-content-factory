/**
 * Tên file: AudienceIndex.ts
 * Last update: 23/10/2026 20:05 (GMT+7)
 * Vai trò: Quản lý và xây dựng chỉ mục cây phả hệ Audience từ MetadataCache của Obsidian.
 * Được sử dụng khi nào?: Khi plugin khởi động và khi có sự kiện thay đổi file Audience (.md).
 * Output: Cấu trúc Map<string, AudienceNode> phục vụ cho việc render cây phả hệ và biểu đồ.
 * Tóm tắt logic hoạt động: Quét các file trong vault/01-Atomic/Audiences/, trích xuất Frontmatter
 * (audience_level, parent_audience, next_job_step, is_buyer_job) để xây dựng DAG quan hệ cha-con và tiến trình.
 */

import { App, TFile, parseYaml } from "obsidian";

// Nhóm 1: Định nghĩa kiểu dữ liệu cho nút Audience trong cây phả hệ
export interface AudienceNode {
	slug: string;
	displayName: string;
	level: "big" | "little" | "micro";
	parentSlug: string | null;
	childSlugs: string[];
	nextJobStepSlugs: string[];
	isBuyerJob: boolean;
	filePath: string;
}

// Nhóm 2: Lớp quản lý chỉ mục AudienceIndex
export class AudienceIndex {
	private app: App;
	private nodes: Map<string, AudienceNode> = new Map();
	private isInitialized: boolean = false;

	constructor(app: App) {
		this.app = app;
	}

	/**
	 * Khởi tạo chỉ mục bằng cách quét tất cả file trong thư mục Audiences
	 */
	public async initialize(): Promise<void> {
		this.nodes.clear();
		const audienceFiles = this.app.vault.getMarkdownFiles().filter((file: TFile) => {
			const normalizedPath = file.path.replace(/\\/g, "/");
			return normalizedPath.startsWith("01-Atomic/Audiences/") && !file.name.endsWith(".yaml");
		});

		for (const file of audienceFiles) {
			const cache = this.app.metadataCache.getFileCache(file);
			let fm: Record<string, any> | undefined = cache?.frontmatter;

			// Cơ chế Fallback: Nếu MetadataCache chưa kịp nạp, đọc trực tiếp file để bóc tách frontmatter
			if (!fm) {
				try {
					const content = await this.app.vault.read(file);
					if (content.startsWith("---")) {
						const parts = content.split("---", 3);
						if (parts.length >= 3) {
							fm = parseYaml(parts[1]) as Record<string, any>;
						}
					}
				} catch (err) {
					console.warn(`[AudienceIndex] Không thể đọc fallback frontmatter cho ${file.path}:`, err);
				}
			}

			if (!fm) continue;

			const slug = file.basename;
			const displayName = (fm.audience_main_job as string) || slug;
			const level = (fm.audience_level as "big" | "little" | "micro") || "little";

			// Parse parent_audience (hỗ trợ cả định dạng wikilink [[slug]] hoặc slug thuần, loại bỏ alias |)
			let parentSlug: string | null = null;
			if (fm.parent_audience) {
				const parentVal = Array.isArray(fm.parent_audience)
					? fm.parent_audience[0]
					: fm.parent_audience;
				if (typeof parentVal === "string" && parentVal.trim().length > 0) {
					parentSlug = parentVal.replace(/\[\[|\]\]/g, "").split("|")[0].trim();
				}
			}

			// Parse next_job_step
			const nextJobStepSlugs: string[] = [];
			if (Array.isArray(fm.next_job_step)) {
				for (const step of fm.next_job_step) {
					if (typeof step === "string") {
						const cleanStep = step.replace(/\[\[|\]\]/g, "").split("|")[0].trim();
						if (cleanStep.length > 0) {
							nextJobStepSlugs.push(cleanStep);
						}
					}
				}
			}

			// Parse is_buyer_job: chuẩn hóa chặt chẽ cả kiểu boolean lẫn chuỗi text "true"/"false"
			let isBuyerJob = false;
			if (typeof fm.is_buyer_job === "boolean") {
				isBuyerJob = fm.is_buyer_job;
			} else if (typeof fm.is_buyer_job === "string") {
				isBuyerJob = fm.is_buyer_job.trim().toLowerCase() === "true";
			}

			this.nodes.set(slug, {
				slug,
				displayName,
				level,
				parentSlug,
				childSlugs: [],
				nextJobStepSlugs,
				isBuyerJob,
				filePath: file.path,
			});
		}

		// Xây dựng quan hệ hai chiều childSlugs từ parentSlug
		for (const [slug, node] of this.nodes.entries()) {
			if (node.parentSlug && this.nodes.has(node.parentSlug)) {
				const parent = this.nodes.get(node.parentSlug);
				if (parent && !parent.childSlugs.includes(slug)) {
					parent.childSlugs.push(slug);
				}
			}
		}

		this.isInitialized = true;
	}

	// Nhóm 3: Các phương thức truy vấn và điều hướng cây phả hệ
	public getAllNodes(): Map<string, AudienceNode> {
		return this.nodes;
	}

	public getNode(slug: string): AudienceNode | undefined {
		return this.nodes.get(slug);
	}

	public getRootNodes(): AudienceNode[] {
		const roots: AudienceNode[] = [];
		for (const node of this.nodes.values()) {
			if (node.level === "big" || !node.parentSlug) {
				roots.push(node);
			}
		}
		return roots;
	}

	public getAudienceCount(): number {
		return this.nodes.size;
	}

	public getBuyerJobCount(): number {
		let count = 0;
		for (const node of this.nodes.values()) {
			if (node.isBuyerJob) count++;
		}
		return count;
	}

	public getDescendants(slug: string): AudienceNode[] {
		const result: AudienceNode[] = [];
		const queue: string[] = [slug];
		const visited = new Set<string>();

		while (queue.length > 0) {
			const current = queue.shift()!;
			if (visited.has(current)) continue;
			visited.add(current);

			const node = this.nodes.get(current);
			if (node) {
				for (const child of node.childSlugs) {
					if (!visited.has(child)) {
						const childNode = this.nodes.get(child);
						if (childNode) {
							result.push(childNode);
							queue.push(child);
						}
					}
				}
			}
		}
		return result;
	}

	public getAncestors(slug: string): AudienceNode[] {
		const result: AudienceNode[] = [];
		let current = this.nodes.get(slug);
		const visited = new Set<string>();

		while (current && current.parentSlug && !visited.has(current.parentSlug)) {
			visited.add(current.parentSlug);
			const parent = this.nodes.get(current.parentSlug);
			if (parent) {
				result.push(parent);
				current = parent;
			} else {
				break;
			}
		}
		return result;
	}

	public getIsInitialized(): boolean {
		return this.isInitialized;
	}
}
