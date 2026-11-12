/**
 * Tên file: TagIndex.ts
 * Last update: 10/11/2026 19:50 (GMT+7)
 * Vai trò: Quản lý danh mục Pillar và Topic từ file topic_map.yaml của active persona (kèm topic_type và tra cứu theo ID/Label/Aliases).
 * Được sử dụng khi nào?: Khi plugin khởi động và cần ánh xạ quan hệ giữa Pillar, Topic và Audience.
 * Output: Cấu trúc Map<string, TopicNode> (theo ID), Map<string, TopicNode> (theo Label/Aliases) và Map<string, PillarNode>.
 * Tóm tắt logic hoạt động: Quét thư mục personas/ (hỗ trợ cả đường dẫn ngoài vault trên Desktop lẫn trong vault),
 * nạp file topic_map.yaml, bóc tách quan hệ Pillar-Topic-Audience kèm topic_type và cung cấp các hàm truy vấn phân bổ.
 */

import { App, parseYaml } from "obsidian";

// Nhóm 1: Định nghĩa cấu trúc dữ liệu cho Topic và Pillar
export type TopicCategoryType = "knowledge" | "insight" | "needs" | "product" | "event";

export interface TopicNode {
	id: string;
	label: string;
	topicType: TopicCategoryType;
	pillarNames: string[];
	audienceSlugs: string[];
}

export interface PillarNode {
	name: string;
	topicIds: string[];
	audienceSlugs: string[];
}

interface RawTopicEntry {
	id?: string;
	label?: string;
	topic_type?: string;
	aliases?: string[];
	pillar_parents?: string[];
	belongs_to_audience?: string[];
}

interface RawTopicMap {
	topics?: RawTopicEntry[];
}

// Nhóm 2: Lớp quản lý chỉ mục TagIndex
export class TagIndex {
	private app: App;
	private topics: Map<string, TopicNode> = new Map();
	private topicsByLabel: Map<string, TopicNode> = new Map();
	private pillars: Map<string, PillarNode> = new Map();
	private isInitialized: boolean = false;

	constructor(app: App) {
		this.app = app;
	}

	/**
	 * Khởi tạo chỉ mục bằng cách quét và phân tích file topic_map.yaml
	 */
	public async initialize(): Promise<void> {
		this.topics.clear();
		this.topicsByLabel.clear();
		this.pillars.clear();

		const content = await this.readActiveTopicMapContent();
		if (!content) {
			console.warn("[TagIndex] Không tìm thấy hoặc không đọc được nội dung topic_map.yaml từ thư mục personas.");
			this.isInitialized = true;
			return;
		}

		try {
			const parsed = parseYaml(content) as RawTopicMap;

			if (parsed && Array.isArray(parsed.topics)) {
				for (const item of parsed.topics) {
					if (!item.id) continue;

					const id = String(item.id);
					const label = item.label || id;
					const pillarNames = Array.isArray(item.pillar_parents) ? item.pillar_parents : [];

					const rawType = String(item.topic_type || "knowledge").trim().toLowerCase();
					const validTypes: TopicCategoryType[] = ["knowledge", "insight", "needs", "product", "event"];
					const topicType: TopicCategoryType = validTypes.includes(rawType as TopicCategoryType)
						? (rawType as TopicCategoryType)
						: "knowledge";

					// Parse belongs_to_audience: loại bỏ cú pháp wikilink [[slug]] và alias |
					const audienceSlugs: string[] = [];
					if (Array.isArray(item.belongs_to_audience)) {
						for (const rawAudience of item.belongs_to_audience) {
							if (typeof rawAudience === "string") {
								const cleanSlug = rawAudience.replace(/\[\[|\]\]/g, "").split("|")[0].trim();
								if (cleanSlug.length > 0 && !audienceSlugs.includes(cleanSlug)) {
									audienceSlugs.push(cleanSlug);
								}
							}
						}
					}

					const topicNode: TopicNode = {
						id,
						label,
						topicType,
						pillarNames,
						audienceSlugs,
					};

					// Lưu trữ TopicNode theo ID, Label và Aliases
					this.topics.set(id, topicNode);
					this.topicsByLabel.set(label.trim().toLowerCase(), topicNode);
					if (Array.isArray(item.aliases)) {
						for (const al of item.aliases) {
							const cleanAl = String(al || "").trim().toLowerCase();
							if (cleanAl && !this.topicsByLabel.has(cleanAl)) {
								this.topicsByLabel.set(cleanAl, topicNode);
							}
						}
					}

					// Cập nhật cấu trúc PillarNode
					for (const pillarName of pillarNames) {
						if (!this.pillars.has(pillarName)) {
							this.pillars.set(pillarName, {
								name: pillarName,
								topicIds: [],
								audienceSlugs: [],
							});
						}

						const pillar = this.pillars.get(pillarName)!;
						if (!pillar.topicIds.includes(id)) {
							pillar.topicIds.push(id);
						}
						for (const aSlug of audienceSlugs) {
							if (!pillar.audienceSlugs.includes(aSlug)) {
								pillar.audienceSlugs.push(aSlug);
							}
						}
					}
				}
			}
		} catch (err) {
			console.error("[TagIndex] Lỗi khi parse YAML topic_map:", err);
		}

		this.isInitialized = true;
	}

	// Nhóm 3: Các hàm quét tìm vị trí topic_map.yaml ngoài vault và trong vault
	private async readActiveTopicMapContent(): Promise<string | null> {
		// 1. Quét qua Node.js fs (Obsidian Desktop) — hỗ trợ khi personas nằm ngoài vault/
		try {
			const fs = require("fs");
			const path = require("path");
			const adapter = this.app.vault.adapter as any;
			const basePath = adapter?.basePath;

			if (basePath) {
				const factoryRoot = path.resolve(basePath, "..");
				const candidateDirs = [
					path.join(factoryRoot, "personas"),
					path.join(basePath, "personas"),
				];

				for (const personasDir of candidateDirs) {
					if (fs.existsSync(personasDir)) {
						const entries = fs.readdirSync(personasDir, { withFileTypes: true });
						for (const entry of entries) {
							if (entry.isDirectory() && !entry.name.startsWith(".") && !entry.name.startsWith("_")) {
								const topicMapPath = path.join(personasDir, entry.name, "topic_map.yaml");
								if (fs.existsSync(topicMapPath)) {
									return fs.readFileSync(topicMapPath, "utf-8");
								}
							}
						}
					}
				}
			}
		} catch (e) {
			// Bỏ qua nếu môi trường không cho phép gọi require('fs')
		}

		// 2. Quét qua Obsidian Vault Adapter (Fallback)
		try {
			const candidateDirs = ["../personas", "personas"];
			for (const dir of candidateDirs) {
				if (await this.app.vault.adapter.exists(dir)) {
					const list = await this.app.vault.adapter.list(dir);
					for (const folder of list.folders) {
						const base = folder.split(/[\\/]/).pop() || "";
						if (!base.startsWith(".") && !base.startsWith("_")) {
							const candidate = `${folder}/topic_map.yaml`.replace(/\\/g, "/");
							if (await this.app.vault.adapter.exists(candidate)) {
								return await this.app.vault.adapter.read(candidate);
							}
						}
					}
				}
			}
		} catch (e) {
			// Adapter fallback
		}

		return null;
	}

	// Nhóm 4: Các hàm truy vấn chỉ mục TagIndex
	public getTopics(): Map<string, TopicNode> {
		return this.topics;
	}

	public getPillars(): Map<string, PillarNode> {
		return this.pillars;
	}

	public getPillar(name: string): PillarNode | undefined {
		return this.pillars.get(name);
	}

	public getTopicsForAudience(slug: string): TopicNode[] {
		const result: TopicNode[] = [];
		for (const topic of this.topics.values()) {
			if (topic.audienceSlugs.includes(slug)) {
				result.push(topic);
			}
		}
		return result;
	}

	public getPillarsForAudience(slug: string): string[] {
		const pillarSet = new Set<string>();
		for (const topic of this.topics.values()) {
			if (topic.audienceSlugs.includes(slug)) {
				for (const p of topic.pillarNames) {
					pillarSet.add(p);
				}
			}
		}
		return Array.from(pillarSet);
	}

	public getTopicByLabelOrId(key: string): TopicNode | undefined {
		const clean = String(key || "").trim();
		if (!clean) return undefined;
		return this.topics.get(clean) || this.topicsByLabel.get(clean.toLowerCase());
	}

	public getTotalTopicCount(): number {
		return this.topics.size;
	}

	public getIsInitialized(): boolean {
		return this.isInitialized;
	}
}
