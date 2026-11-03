/**
 * Ten file: EngagementStore.ts
 * Last update: 03/11/2026 15:24 (GMT+7)
 * Vai tro: Tang du lieu doc/ghi/truy van da chieu engagement tu file JSONL va bo dem Facebook Tracker trong vault.
 * Duoc su dung khi nao?: Khi plugin khoi dong, khi user nhap du lieu, khi cac view bieu do can truy van da chieu.
 * Output: Cac phuong thuc truy van engagement theo thoi gian (Ngay/Tuan/Thang), chi so (Score/Likes/Comments/Shares/Avg),
 *         nguon (Thuong hieu/Doi thu/Khac/Nhan tuy chinh/Tung Trang), va xep hang da chieu.
 * Tom tat logic hoat dong: Doc file JSONL trong .content-pipeline/engagement/, ket hop quet YAML frontmatter trong vault
 *          va du lieu thuc te tu .content-pipeline/fb-tracker-state.json + fb-watchlist.json, dong bo nhan phan loai xuyen suot moi bang.
 */

import { App, TFile, parseYaml } from "obsidian";
import { TagIndex } from "./TagIndex";

// Nhom 1: Dinh nghia cac interface du lieu engagement & Bo loc da chieu
export interface EngagementMetrics {
	likes: number;
	comments: number;
	shares: number;
	views: number;
}

export interface EngagementRecord {
	post_id: string;
	platform: string;
	collected_at: string; // ISO 8601
	metrics: EngagementMetrics;
}

export type ChartMetricType = "score" | "likes" | "comments" | "shares" | "avg_score" | "posts";
export type TimelineGroupBy = "day" | "week" | "month" | "year";
export type TimelineBreakdownBy = "metric" | "source" | "audience";
export type RankingDimension = "post" | "author" | "tag" | "audience" | "pillar";
export type ComponentMetricKey = "likes" | "comments" | "shares";

export const UNASSIGNED_AUDIENCE_KEY = "__unassigned__";

export interface TimelineQueryOptions {
	groupBy: TimelineGroupBy;
	days: number; // 0 = Tat ca thoi gian (neu khong truyen startDate/endDate)
	startDate?: string; // YYYY-MM-DD
	endDate?: string; // YYYY-MM-DD
	metric: ChartMetricType;
	dateBasis: "published" | "collected";
	sourceFilter: string; // "all" | "own" | "external" | "author:<name>"
	sourceFilters?: string[]; // Bo loc da chon: ["own", "external", "author:<name>"]
	filterAudience?: string;
	filterAudiences?: string[]; // Bo loc da chon Audience slug hoac UNASSIGNED_AUDIENCE_KEY
}

export interface TimelinePoint {
	period: string;
	totalScore: number;
	value: number;
	likes: number;
	comments: number;
	shares: number;
	recordCount: number;
}

export interface TimelineSeries {
	key: string;
	label: string;
	color: string;
	points: TimelinePoint[];
	totalValue: number;
}

export interface MultiSeriesTimelineQueryOptions {
	groupBy: TimelineGroupBy;
	days: number;
	startDate?: string;
	endDate?: string;
	dateBasis: "published" | "collected";
	breakdownBy: TimelineBreakdownBy;
	metrics: ChartMetricType[];
	sourceFilters: string[];
	filterAudiences: string[];
	audienceLabelMap?: Map<string, string>;
}

export interface TimelineSummaryKpi {
	totalScore: number;
	totalLikes: number;
	totalComments: number;
	totalShares: number;
	postCount: number;
	avgScorePerPost: number;
}

export interface RankingQueryOptions {
	dimension: RankingDimension;
	metric: Exclude<ChartMetricType, "posts">;
	days: number; // 0 = Tat ca
	startDate?: string; // YYYY-MM-DD
	endDate?: string; // YYYY-MM-DD
	dateBasis?: "published" | "collected";
	limit: number;
	sourceFilter: string; // "all" | "own" | "external"
	sourceFilters?: string[]; // Multi-select nguon/trang
	filterAudiences?: string[]; // Multi-select audience
	selectedMetrics?: ComponentMetricKey[]; // Phan ra thanh phan Likes/Comments/Shares
}

export interface TagRankEntry {
	tag: string;
	sublabel?: string;
	url?: string;
	score: number;
	value: number;
	likes: number;
	comments: number;
	shares: number;
	postCount: number;
}

export interface PostSparkline5D {
	dailyScores: Array<number | null>; // 5 diem tuong ung [D-4, D-3, D-2, D-1, Hom nay]; null = khong co du lieu o ngay do
	dayLabels: string[]; // Nhan DD/MM cho 5 ngay
	delta5d: number | null; // Muc tang truong giua moc ngay dau tien co du lieu va moc cuoi cung (null neu chi co 1 moc)
	validDaysCount: number; // So ngay thuc te co du lieu trong 5 ngay gan nhat
	totalScanCount: number; // Tong so ban ghi quet cua bai viet
	isFirstScan: boolean; // True khi bai viet chi co 1 moc ngay du lieu (moi quet lan dau, chua co du lieu cac ngay truoc)
}

export interface TimelinePeriodPostItem {
	postId: string;
	watchId?: string;
	fbPostId?: string;
	vaultSlug?: string;
	titleSnippet: string;
	authorName: string;
	sourceType: string;
	url: string;
	publishedAt?: string;
	collectedAt: string;
	score: number;
	likes: number;
	comments: number;
	shares: number;
}

// Nhom 2: Hang so cau hinh
const ENGAGEMENT_DIR = ".content-pipeline/engagement";
const SCORE_WEIGHTS = { likes: 1, comments: 2, shares: 3 };

// Nhom 3: Interface noi bo map post metadata
interface PostMeta {
	inVault: boolean; // Chi true khi bai viet da duoc luu thanh file .md trong Vault
	audiences: string[];
	tags: string[];
	pillars: string[];
	authorName: string;
	sourceType: string; // "own" | "external" | "other" | Nhan do user tu tao
	titleSnippet: string;
	url: string;
	publishedAt?: string; // ISO 8601
	watchId?: string;
	fbPostId?: string;
	vaultSlug?: string;
}

export function formatSourceTypeLabel(rawType?: string): string {
	const v = String(rawType || "external").trim();
	if (!v || v === "external") return "Đối thủ";
	if (v === "own") return "Thương hiệu";
	if (v === "other") return "Khác";
	if (v.startsWith("source_type:")) return v.slice(12);
	return v;
}

// Nhom 4: Lop EngagementStore
export class EngagementStore {
	private app: App;
	private tagIndex: TagIndex | null;
	private records: EngagementRecord[] = [];
	private postMetaMap: Map<string, PostMeta> = new Map();
	private knownAuthors: Set<string> = new Set();
	private customSourceLabels: Set<string> = new Set();
	private isInitialized: boolean = false;

	constructor(app: App, tagIndex?: TagIndex) {
		this.app = app;
		this.tagIndex = tagIndex || null;
	}

	// --- Nhom 5: Khoi tao va doc du lieu ---

	async initialize(): Promise<void> {
		this.records = [];
		this.postMetaMap.clear();
		this.knownAuthors.clear();
		this.customSourceLabels.clear();
		await this.loadEngagementFiles();
		await this.buildPostMetaMap();
		this.isInitialized = true;
		console.log(`[EngagementStore] Loaded ${this.records.length} records, ${this.postMetaMap.size} post mappings.`);
	}

	private async loadEngagementFiles(): Promise<void> {
		try {
			const dirExists = await this.app.vault.adapter.exists(ENGAGEMENT_DIR);
			if (!dirExists) return;

			const listing = await this.app.vault.adapter.list(ENGAGEMENT_DIR);
			for (const filePath of listing.files) {
				if (!filePath.endsWith(".json")) continue;
				try {
					const content = await this.app.vault.adapter.read(filePath);
					const lines = content.split("\n").filter((l: string) => l.trim().length > 0);
					for (const line of lines) {
						try {
							const record = JSON.parse(line) as EngagementRecord;
							if (record.post_id && record.metrics) {
								this.records.push(record);
							}
						} catch {
							// Bo qua dong JSON loi
						}
					}
				} catch {
					// Bo qua file khong doc duoc
				}
			}
		} catch {
			// Thu muc khong ton tai
		}
	}

	// Quet cac file bai viet trong Vault (03-Content/) de lay tags/audience_target va hop nhat metadata tu fb-tracker-state.json
	private async buildPostMetaMap(): Promise<void> {
		const resolvePillars = (audiences: string[]): string[] => {
			const pillars: string[] = [];
			if (this.tagIndex) {
				for (const aSlug of audiences) {
					const pNames = this.tagIndex.getPillarsForAudience(aSlug);
					for (const p of pNames) {
						if (!pillars.includes(p)) pillars.push(p);
					}
				}
			}
			return pillars;
		};

		// 1. Quet cac file bai viet Markdown da luu trong Vault (Nguon duy nhat cho tags, audience_target, pillars)
		const files = this.app.vault.getMarkdownFiles();
		for (const file of files) {
			const normPath = file.path.replace(/\\/g, "/");
			if (normPath.startsWith("01-Atomic/")) continue;

			const cache = this.app.metadataCache.getFileCache(file);
			let fm: Record<string, any> | undefined = cache?.frontmatter;

			if (!fm && normPath.startsWith("03-Content/")) {
				try {
					const content = await this.app.vault.read(file);
					if (content.startsWith("---")) {
						const parts = content.split("---", 3);
						if (parts.length >= 3) {
							fm = parseYaml(parts[1]) as Record<string, any>;
						}
					}
				} catch {
					// Bo qua
				}
			}

			if (!fm) continue;

			const hasAudienceTarget = Array.isArray(fm.audience_target) && fm.audience_target.length > 0;
			const hasTags = Array.isArray(fm.tags) && fm.tags.length > 0;
			const hasFbPostId =
				fm.fb_post_id !== undefined && fm.fb_post_id !== null && String(fm.fb_post_id).trim().length > 0;
			if (!hasAudienceTarget && !hasTags && !hasFbPostId) continue;

			const postId = file.basename;
			const audiences: string[] = [];
			const tags: string[] = [];

			if (hasAudienceTarget) {
				for (const raw of fm.audience_target) {
					const clean = String(raw).replace(/\[\[|\]\]/g, "").split("|")[0].trim();
					if (clean.length > 0 && !audiences.includes(clean)) {
						audiences.push(clean);
					}
				}
			}

			// Chi lay DUNG truong tags trong YAML Frontmatter cua bai viet da luu trong Vault
			if (hasTags) {
				for (const t of fm.tags) {
					if (typeof t === "string" && t.trim().length > 0) {
						const cleanTag = t.trim();
						if (!tags.includes(cleanTag)) {
							tags.push(cleanTag);
						}
					}
				}
			}

			const titleStr = String(fm.title || file.basename);
			const authorName = String(fm.author || "Vault Post").trim();
			if (authorName) this.knownAuthors.add(authorName);
			const rawFmSource = fm.source_type ? String(fm.source_type).trim() : "";
			const sourceType: string = rawFmSource
				? rawFmSource
				: normPath.startsWith("03-Content/Posted")
					? "own"
					: "external";
			if (sourceType && !["own", "external", "other"].includes(sourceType)) {
				this.customSourceLabels.add(sourceType);
			}
			const publishedAt = fm.publish_date ? new Date(String(fm.publish_date)).toISOString() : undefined;

			const pillars = resolvePillars(audiences);
			const fbIdStr = hasFbPostId ? String(fm.fb_post_id).trim() : undefined;
			const metaObj: PostMeta = {
				inVault: true,
				audiences,
				tags,
				pillars,
				authorName,
				sourceType,
				titleSnippet: titleStr,
				url: String(fm.fb_url || ""),
				publishedAt,
				fbPostId: fbIdStr,
				vaultSlug: postId,
			};
			this.postMetaMap.set(postId, metaObj);
			if (fbIdStr) {
				this.postMetaMap.set(fbIdStr, metaObj);
			}
		}

		// 2. Bo sung thong tin Tieu de / Tac gia / Ngay dang / Nhan phan loai tu fb-watchlist.json & fb-tracker-state.json
		try {
			const wlPath = ".content-pipeline/fb-watchlist.json";
			const stPath = ".content-pipeline/fb-tracker-state.json";
			const watchSourceMap = new Map<string, { sourceType: string; url: string; fromPage?: string }>();
			const pageSourceById = new Map<string, string>();
			const pageSourceByIdent = new Map<string, string>();

			if (await this.app.vault.adapter.exists(wlPath)) {
				const wl = JSON.parse(await this.app.vault.adapter.read(wlPath));
				if (Array.isArray(wl?.settings?.custom_source_labels)) {
					for (const lbl of wl.settings.custom_source_labels) {
						const clean = String(lbl || "").trim();
						if (clean && !["own", "external", "other"].includes(clean)) {
							this.customSourceLabels.add(clean);
						}
					}
				}
				for (const pg of wl?.pages || []) {
					const stype = String(pg?.source_type || "external").trim() || "external";
					if (!["own", "external", "other"].includes(stype)) {
						this.customSourceLabels.add(stype);
					}
					if (pg?.id) pageSourceById.set(pg.id, stype);
					if (pg?.page_identifier) pageSourceByIdent.set(pg.page_identifier, stype);
				}
				for (const p of wl?.posts || []) {
					if (p?.id) {
						const stype = String(p.source_type || "external").trim() || "external";
						if (!["own", "external", "other"].includes(stype)) {
							this.customSourceLabels.add(stype);
						}
						watchSourceMap.set(p.id, {
							sourceType: stype,
							url: String(p.url || ""),
							fromPage: p.from_page_name || p.from_page,
						});
					}
				}
			}

			if (await this.app.vault.adapter.exists(stPath)) {
				const st = JSON.parse(await this.app.vault.adapter.read(stPath));
				for (const d of st?.discovered_posts || []) {
					if (d?.id) {
						const inheritedPageType =
							(d.from_page_id && pageSourceById.get(d.from_page_id)) ||
							(d.from_page && pageSourceByIdent.get(d.from_page)) ||
							String(d.source_type || "external").trim() ||
							"external";
						if (!["own", "external", "other"].includes(inheritedPageType)) {
							this.customSourceLabels.add(inheritedPageType);
						}
						watchSourceMap.set(d.id, {
							sourceType: inheritedPageType,
							url: String(d.url || ""),
							fromPage: d.from_page_name || d.from_page,
						});
					}
				}

				const postsObj = st?.posts || {};
				for (const watchId of Object.keys(postsObj)) {
					const pState = postsObj[watchId];
					if (!pState) continue;
					const slug = pState.vault_slug ? String(pState.vault_slug) : "";
					const fbId = pState.fb_post_id ? String(pState.fb_post_id) : "";
					const wInfo = watchSourceMap.get(watchId);

					const authorName = String(pState.author_name || wInfo?.fromPage || "Facebook").trim();
					if (authorName) this.knownAuthors.add(authorName);
					const sourceType: string =
						wInfo?.sourceType || String(pState.source_type || "external").trim() || "external";
					const snippet = String(pState.title_snippet || slug || fbId || "Bài viết Facebook");
					const publishedAt = pState.creation_time
						? new Date(Number(pState.creation_time) * 1000).toISOString()
						: undefined;

					const existingMeta =
						(slug && this.postMetaMap.get(slug)) || (fbId && this.postMetaMap.get(fbId)) || null;

					const finalMeta: PostMeta = {
						inVault: existingMeta ? existingMeta.inVault : false,
						audiences: existingMeta ? existingMeta.audiences : [],
						tags: existingMeta ? existingMeta.tags : [],
						pillars: existingMeta ? existingMeta.pillars : [],
						authorName: existingMeta?.authorName && existingMeta.authorName !== "Vault Post"
							? existingMeta.authorName
							: authorName,
						sourceType: wInfo?.sourceType || existingMeta?.sourceType || sourceType,
						titleSnippet: snippet,
						url: wInfo?.url || existingMeta?.url || (fbId ? `https://www.facebook.com/${fbId}` : ""),
						publishedAt: publishedAt || existingMeta?.publishedAt,
						watchId,
						fbPostId: fbId || existingMeta?.fbPostId,
						vaultSlug: slug || existingMeta?.vaultSlug,
					};

					this.postMetaMap.set(watchId, finalMeta);
					if (slug) this.postMetaMap.set(slug, finalMeta);
					if (fbId) this.postMetaMap.set(fbId, finalMeta);
					if (existingMeta?.vaultSlug) this.postMetaMap.set(existingMeta.vaultSlug, finalMeta);
				}
			}
		} catch {
			// Bo qua neu file chua ton tai
		}
	}

	public getKnownAuthors(): string[] {
		return Array.from(this.knownAuthors).sort((a, b) => a.localeCompare(b));
	}

	public getCustomSourceLabels(): string[] {
		return Array.from(this.customSourceLabels).sort((a, b) => a.localeCompare(b));
	}

	public getSourceTypeFilterOptions(): Array<{ value: string; label: string; group: string; color: string }> {
		const CUSTOM_COLORS = ["#30d158", "#bf5af2", "#ff375f", "#64d2ff", "#ffd60a", "#ac8e68"];
		const opts: Array<{ value: string; label: string; group: string; color: string }> = [
			{ value: "own", label: "Chỉ Thương hiệu", group: "Phân loại nguồn", color: "#0a84ff" },
			{ value: "external", label: "Chỉ Đối thủ", group: "Phân loại nguồn", color: "#ff9f0a" },
			{ value: "other", label: "Chỉ Khác", group: "Phân loại nguồn", color: "#8e8e93" },
		];
		const customs = this.getCustomSourceLabels();
		customs.forEach((lbl, idx) => {
			opts.push({
				value: `source_type:${lbl}`,
				label: `Chỉ ${lbl}`,
				group: "Phân loại nguồn",
				color: CUSTOM_COLORS[idx % CUSTOM_COLORS.length],
			});
		});
		return opts;
	}

	// --- Nhom 6: Ghi du lieu ---

	async addRecord(record: EngagementRecord): Promise<void> {
		const date = new Date(record.collected_at);
		const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
		const filePath = `${ENGAGEMENT_DIR}/${monthKey}.json`;

		const dirExists = await this.app.vault.adapter.exists(ENGAGEMENT_DIR);
		if (!dirExists) {
			const parentDir = ".content-pipeline";
			const parentExists = await this.app.vault.adapter.exists(parentDir);
			if (!parentExists) {
				await this.app.vault.adapter.mkdir(parentDir);
			}
			await this.app.vault.adapter.mkdir(ENGAGEMENT_DIR);
		}

		const line = JSON.stringify(record);
		const fileExists = await this.app.vault.adapter.exists(filePath);
		if (fileExists) {
			const existing = await this.app.vault.adapter.read(filePath);
			await this.app.vault.adapter.write(filePath, existing.trimEnd() + "\n" + line + "\n");
		} else {
			await this.app.vault.adapter.write(filePath, line + "\n");
		}

		this.records.push(record);
	}

	async addRecords(records: EngagementRecord[]): Promise<void> {
		for (const record of records) {
			await this.addRecord(record);
		}
	}

	// --- Nhom 7: Tinh diem & Bo loc co so ---

	private calcScore(metrics: EngagementMetrics): number {
		return (
			(metrics.likes || 0) * SCORE_WEIGHTS.likes +
			(metrics.comments || 0) * SCORE_WEIGHTS.comments +
			(metrics.shares || 0) * SCORE_WEIGHTS.shares
		);
	}

	private filterByDays(
		days: number,
		dateBasis: "published" | "collected" = "collected",
		startDate?: string,
		endDate?: string
	): EngagementRecord[] {
		if (startDate && endDate) {
			const startTs = new Date(`${startDate}T00:00:00`).getTime();
			const endTs = new Date(`${endDate}T23:59:59.999`).getTime();
			return this.records.filter((r) => {
				const meta = this.postMetaMap.get(r.post_id);
				const rawDate = dateBasis === "published" && meta?.publishedAt ? meta.publishedAt : r.collected_at;
				const ts = new Date(rawDate).getTime();
				return ts >= startTs && ts <= endTs;
			});
		}
		if (!days || days <= 0) return [...this.records];
		const cutoff = Date.now() - days * 86400000;
		return this.records.filter((r) => {
			const meta = this.postMetaMap.get(r.post_id);
			const rawDate = dateBasis === "published" && meta?.publishedAt ? meta.publishedAt : r.collected_at;
			return new Date(rawDate).getTime() >= cutoff;
		});
	}

	private matchesSingleSourceToken(postId: string, token: string): boolean {
		if (!token || token === "all") return true;
		const meta = this.postMetaMap.get(postId);
		if (!meta) return token === "external";
		if (token === "own" || token === "external" || token === "other") {
			return meta.sourceType === token;
		}
		if (token.startsWith("source_type:")) {
			const targetType = token.slice(12);
			return meta.sourceType === targetType;
		}
		if (token.startsWith("author:")) {
			const targetAuthor = token.slice(7);
			return meta.authorName === targetAuthor;
		}
		return meta.sourceType === token;
	}

	private matchesSourceFilter(postId: string, sourceFilter: string, sourceFilters?: string[]): boolean {
		if (Array.isArray(sourceFilters) && sourceFilters.length > 0) {
			if (sourceFilters.includes("all")) return true;
			return sourceFilters.some((tok) => this.matchesSingleSourceToken(postId, tok));
		}
		return this.matchesSingleSourceToken(postId, sourceFilter);
	}

	private matchesAudienceFilter(postId: string, singleAudience?: string, multiAudiences?: string[]): boolean {
		const meta = this.postMetaMap.get(postId);
		if (Array.isArray(multiAudiences) && multiAudiences.length > 0) {
			const postAuds = meta?.inVault ? meta.audiences : [];
			if (postAuds.length === 0) {
				return multiAudiences.includes(UNASSIGNED_AUDIENCE_KEY);
			}
			return postAuds.some((a) => multiAudiences.includes(a));
		}
		if (singleAudience) {
			if (singleAudience === UNASSIGNED_AUDIENCE_KEY) {
				return !meta || !meta.inVault || meta.audiences.length === 0;
			}
			return Boolean(meta && meta.inVault && meta.audiences.includes(singleAudience));
		}
		return true;
	}

	private getLatestRecordsByPost(records: EngagementRecord[]): EngagementRecord[] {
		const latestMap = new Map<string, EngagementRecord>();
		for (const rec of records) {
			const prev = latestMap.get(rec.post_id);
			if (!prev || new Date(rec.collected_at).getTime() >= new Date(prev.collected_at).getTime()) {
				latestMap.set(rec.post_id, rec);
			}
		}
		return Array.from(latestMap.values());
	}

	// --- Nhom 8: Truy van tong hop ---

	getScoreByAudience(audienceSlug: string, days: number = 90): number {
		const recent = this.getLatestRecordsByPost(this.filterByDays(days));
		let total = 0;
		for (const rec of recent) {
			const meta = this.postMetaMap.get(rec.post_id);
			if (meta && meta.audiences.includes(audienceSlug)) {
				total += this.calcScore(rec.metrics);
			}
		}
		return total;
	}

	getScoreByPillar(pillarName: string, days: number = 90): number {
		const recent = this.getLatestRecordsByPost(this.filterByDays(days));
		let total = 0;
		for (const rec of recent) {
			const meta = this.postMetaMap.get(rec.post_id);
			if (meta && meta.pillars.includes(pillarName)) {
				total += this.calcScore(rec.metrics);
			}
		}
		return total;
	}

	getScoreByTag(tag: string, days: number = 90): number {
		const recent = this.getLatestRecordsByPost(this.filterByDays(days));
		let total = 0;
		for (const rec of recent) {
			const meta = this.postMetaMap.get(rec.post_id);
			if (meta && meta.tags.includes(tag)) {
				total += this.calcScore(rec.metrics);
			}
		}
		return total;
	}

	getTotalScore(days: number = 90): number {
		const recent = this.getLatestRecordsByPost(this.filterByDays(days));
		let total = 0;
		for (const rec of recent) {
			total += this.calcScore(rec.metrics);
		}
		return total;
	}

	// --- Nhom 9: Truy van Timeline Da chieu & KPI Summary ---

	public queryTimelineAdvanced(opts: TimelineQueryOptions): {
		points: TimelinePoint[];
		summary: TimelineSummaryKpi;
	} {
		const filteredByTime = this.filterByDays(opts.days, opts.dateBasis, opts.startDate, opts.endDate);
		const matchingRecords = filteredByTime.filter((rec) => {
			if (!this.matchesSourceFilter(rec.post_id, opts.sourceFilter, opts.sourceFilters)) return false;
			if (!this.matchesAudienceFilter(rec.post_id, opts.filterAudience, opts.filterAudiences)) return false;
			return true;
		});

		// Tinh KPI Summary tren ban ghi moi nhat cua moi bai viet
		const uniquePosts = this.getLatestRecordsByPost(matchingRecords);
		let totalScore = 0;
		let totalLikes = 0;
		let totalComments = 0;
		let totalShares = 0;
		for (const r of uniquePosts) {
			totalScore += this.calcScore(r.metrics);
			totalLikes += r.metrics.likes || 0;
			totalComments += r.metrics.comments || 0;
			totalShares += r.metrics.shares || 0;
		}
		const postCount = uniquePosts.length;
		const avgScorePerPost = postCount > 0 ? Math.round(totalScore / postCount) : 0;

		// Nhom theo period -> post_id -> ban ghi moi nhat trong ky do
		const periodPostMap = new Map<string, Map<string, EngagementRecord>>();
		const recordsToGroup = opts.dateBasis === "published" ? uniquePosts : matchingRecords;

		for (const rec of recordsToGroup) {
			const meta = this.postMetaMap.get(rec.post_id);
			const rawDateStr =
				opts.dateBasis === "published" && meta?.publishedAt ? meta.publishedAt : rec.collected_at;
			const date = new Date(rawDateStr);
			if (isNaN(date.getTime())) continue;

			let period: string;
			if (opts.groupBy === "day") {
				period = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
			} else if (opts.groupBy === "month") {
				period = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
			} else if (opts.groupBy === "year") {
				period = String(date.getFullYear());
			} else {
				const startOfYear = new Date(date.getFullYear(), 0, 1);
				const dayOfYear = Math.floor((date.getTime() - startOfYear.getTime()) / 86400000);
				const weekNum = Math.ceil((dayOfYear + startOfYear.getDay() + 1) / 7);
				period = `${date.getFullYear()}-W${String(weekNum).padStart(2, "0")}`;
			}

			if (!periodPostMap.has(period)) {
				periodPostMap.set(period, new Map<string, EngagementRecord>());
			}
			const postMap = periodPostMap.get(period)!;
			const prev = postMap.get(rec.post_id);
			if (!prev || new Date(rec.collected_at).getTime() >= new Date(prev.collected_at).getTime()) {
				postMap.set(rec.post_id, rec);
			}
		}

		const points: TimelinePoint[] = [];
		for (const [period, postMap] of periodPostMap.entries()) {
			let pScore = 0;
			let pLikes = 0;
			let pComments = 0;
			let pShares = 0;
			for (const rec of postMap.values()) {
				pScore += this.calcScore(rec.metrics);
				pLikes += rec.metrics.likes || 0;
				pComments += rec.metrics.comments || 0;
				pShares += rec.metrics.shares || 0;
			}
			const cnt = postMap.size;
			let val = pScore;
			if (opts.metric === "likes") val = pLikes;
			else if (opts.metric === "comments") val = pComments;
			else if (opts.metric === "shares") val = pShares;
			else if (opts.metric === "avg_score") val = cnt > 0 ? Math.round(pScore / cnt) : 0;
			else if (opts.metric === "posts") val = cnt;

			points.push({
				period,
				totalScore: pScore,
				value: val,
				likes: pLikes,
				comments: pComments,
				shares: pShares,
				recordCount: cnt,
			});
		}

		points.sort((a, b) => a.period.localeCompare(b.period));

		return {
			points,
			summary: {
				totalScore,
				totalLikes,
				totalComments,
				totalShares,
				postCount,
				avgScorePerPost,
			},
		};
	}

	// Truy van Da tuyen (Multi-Series) phuc vu TimelineChartView (Tach duong theo Chi so | Nguon/Trang | Audience)
	public queryTimelineMultiSeries(opts: MultiSeriesTimelineQueryOptions): {
		periods: string[];
		series: TimelineSeries[];
		summary: TimelineSummaryKpi;
	} {
		const SERIES_PALETTE = [
			"#0a84ff", // Blue
			"#5e5ce6", // Indigo
			"#30d158", // Green
			"#ff9f0a", // Orange
			"#ff375f", // Pink
			"#64d2ff", // Cyan
			"#bf5af2", // Purple
			"#ffd60a", // Yellow
			"#ac8e68", // Brown
			"#ff453a", // Red
		];

		const METRIC_INFO: Record<ChartMetricType, { label: string; color: string }> = {
			score: { label: "Tổng Điểm (Score)", color: "#0a84ff" },
			avg_score: { label: "TB Score / bài", color: "#64d2ff" },
			likes: { label: "Lượt thích (Likes)", color: "#5e5ce6" },
			comments: { label: "Bình luận (Comments)", color: "#30d158" },
			shares: { label: "Chia sẻ (Shares)", color: "#ff9f0a" },
			posts: { label: "Số lượng bài viết", color: "#ff375f" },
		};

		// 1. Tinh KPI Summary chung cho toan bo tap du lieu thoa man bo loc
		const baseResult = this.queryTimelineAdvanced({
			groupBy: opts.groupBy,
			days: opts.days,
			startDate: opts.startDate,
			endDate: opts.endDate,
			metric: opts.metrics[0] || "score",
			dateBasis: opts.dateBasis,
			sourceFilter: "all",
			sourceFilters: opts.sourceFilters,
			filterAudiences: opts.filterAudiences,
		});

		const allPeriodsSet = new Set<string>(baseResult.points.map((p) => p.period));
		const rawSeriesList: Array<{
			key: string;
			label: string;
			color: string;
			pointMap: Map<string, TimelinePoint>;
		}> = [];

		const activeMetrics: ChartMetricType[] =
			opts.metrics && opts.metrics.length > 0 ? opts.metrics : ["score"];
		const primaryMetric: ChartMetricType = activeMetrics[0] || "score";

		if (opts.breakdownBy === "metric") {
			// Moi Chi so trong activeMetrics la 1 duong bieu dien tren cung tap du lieu loc
			for (const m of activeMetrics) {
				const res = this.queryTimelineAdvanced({
					groupBy: opts.groupBy,
					days: opts.days,
					startDate: opts.startDate,
					endDate: opts.endDate,
					metric: m,
					dateBasis: opts.dateBasis,
					sourceFilter: "all",
					sourceFilters: opts.sourceFilters,
					filterAudiences: opts.filterAudiences,
				});
				const pMap = new Map<string, TimelinePoint>();
				for (const pt of res.points) {
					allPeriodsSet.add(pt.period);
					pMap.set(pt.period, pt);
				}
				const info = METRIC_INFO[m] || { label: m, color: "#0a84ff" };
				rawSeriesList.push({
					key: `metric:${m}`,
					label: info.label,
					color: info.color,
					pointMap: pMap,
				});
			}
		} else if (opts.breakdownBy === "source") {
			// Xac dinh danh sach nguon can tach duong
			let targetSources = [...opts.sourceFilters];
			if (targetSources.length === 0) {
				const authors = this.getKnownAuthors();
				if (authors.length > 0) {
					targetSources = authors.slice(0, 8).map((a) => `author:${a}`);
				} else {
					targetSources = ["own", "external"];
				}
			}

			targetSources.forEach((srcToken, idx) => {
				const res = this.queryTimelineAdvanced({
					groupBy: opts.groupBy,
					days: opts.days,
					startDate: opts.startDate,
					endDate: opts.endDate,
					metric: primaryMetric,
					dateBasis: opts.dateBasis,
					sourceFilter: srcToken,
					filterAudiences: opts.filterAudiences,
				});
				const pMap = new Map<string, TimelinePoint>();
				for (const pt of res.points) {
					allPeriodsSet.add(pt.period);
					pMap.set(pt.period, pt);
				}
				let label = srcToken;
				if (srcToken.startsWith("author:")) label = srcToken.slice(7);
				else label = formatSourceTypeLabel(srcToken);

				rawSeriesList.push({
					key: `source:${srcToken}`,
					label,
					color: SERIES_PALETTE[idx % SERIES_PALETTE.length],
					pointMap: pMap,
				});
			});
		} else if (opts.breakdownBy === "audience") {
			// Xac dinh danh sach Audience can tach duong
			let targetAudiences = [...opts.filterAudiences];
			if (targetAudiences.length === 0) {
				const discoveredAuds = new Set<string>();
				for (const meta of this.postMetaMap.values()) {
					if (meta.inVault && meta.audiences.length > 0) {
						meta.audiences.forEach((a) => discoveredAuds.add(a));
					}
				}
				if (discoveredAuds.size > 0) {
					targetAudiences = Array.from(discoveredAuds).slice(0, 8);
				} else {
					targetAudiences = [UNASSIGNED_AUDIENCE_KEY];
				}
			}

			targetAudiences.forEach((audKey, idx) => {
				const res = this.queryTimelineAdvanced({
					groupBy: opts.groupBy,
					days: opts.days,
					startDate: opts.startDate,
					endDate: opts.endDate,
					metric: primaryMetric,
					dateBasis: opts.dateBasis,
					sourceFilter: "all",
					sourceFilters: opts.sourceFilters,
					filterAudiences: [audKey],
				});
				const pMap = new Map<string, TimelinePoint>();
				for (const pt of res.points) {
					allPeriodsSet.add(pt.period);
					pMap.set(pt.period, pt);
				}
				const label =
					audKey === UNASSIGNED_AUDIENCE_KEY
						? "Chưa gắn Audience (Ngoài Vault)"
						: opts.audienceLabelMap?.get(audKey) || audKey;

				rawSeriesList.push({
					key: `audience:${audKey}`,
					label,
					color: SERIES_PALETTE[idx % SERIES_PALETTE.length],
					pointMap: pMap,
				});
			});
		}

		const sortedPeriods = Array.from(allPeriodsSet).sort((a, b) => a.localeCompare(b));

		// Dong bo hoa tat ca cac duong tren cung mang sortedPeriods
		const finalSeries: TimelineSeries[] = rawSeriesList.map((raw) => {
			let totalVal = 0;
			const alignedPoints: TimelinePoint[] = sortedPeriods.map((period) => {
				const found = raw.pointMap.get(period);
				if (found) {
					totalVal += found.value;
					return found;
				}
				return {
					period,
					totalScore: 0,
					value: 0,
					likes: 0,
					comments: 0,
					shares: 0,
					recordCount: 0,
				};
			});
			return {
				key: raw.key,
				label: raw.label,
				color: raw.color,
				points: alignedPoints,
				totalValue: totalVal,
			};
		});

		return {
			periods: sortedPeriods,
			series: finalSeries,
			summary: baseResult.summary,
		};
	}

	/**
	 * Truy van danh sach bai viet chi tiet cua 1 moc thoi gian (targetPeriod) va 1 duong bieu dien (seriesKey).
	 * Neu bieu do dang ve theo Nguon/Trang (seriesKey = "source:<token>") hoac Audience (seriesKey = "audience:<slug>"),
	 * ham se chi tra ve dung cac bai viet thuoc Nguon hoac Audience do tai moc thoi gian duoc chon.
	 */
	public queryTimelinePeriodPosts(opts: {
		targetPeriod: string;
		seriesKey: string;
		groupBy: TimelineGroupBy;
		days: number;
		startDate?: string;
		endDate?: string;
		dateBasis: "published" | "collected";
		sourceFilters: string[];
		filterAudiences: string[];
	}): TimelinePeriodPostItem[] {
		let effectiveSourceFilter = "all";
		let effectiveSourceFilters: string[] | undefined = opts.sourceFilters;
		let effectiveAudiences: string[] | undefined = opts.filterAudiences;

		if (opts.seriesKey.startsWith("source:")) {
			effectiveSourceFilter = opts.seriesKey.slice(7);
			effectiveSourceFilters = undefined;
		} else if (opts.seriesKey.startsWith("audience:")) {
			const audKey = opts.seriesKey.slice(9);
			effectiveAudiences = [audKey];
		}

		const filteredByTime = this.filterByDays(opts.days, opts.dateBasis, opts.startDate, opts.endDate);
		const matchingRecords = filteredByTime.filter((rec) => {
			if (!this.matchesSourceFilter(rec.post_id, effectiveSourceFilter, effectiveSourceFilters)) return false;
			if (!this.matchesAudienceFilter(rec.post_id, undefined, effectiveAudiences)) return false;
			return true;
		});

		const uniquePosts = this.getLatestRecordsByPost(matchingRecords);
		const recordsToGroup = opts.dateBasis === "published" ? uniquePosts : matchingRecords;
		const postMap = new Map<string, EngagementRecord>();

		for (const rec of recordsToGroup) {
			const meta = this.postMetaMap.get(rec.post_id);
			const rawDateStr =
				opts.dateBasis === "published" && meta?.publishedAt ? meta.publishedAt : rec.collected_at;
			const date = new Date(rawDateStr);
			if (isNaN(date.getTime())) continue;

			let period: string;
			if (opts.groupBy === "day") {
				period = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
			} else if (opts.groupBy === "month") {
				period = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
			} else if (opts.groupBy === "year") {
				period = String(date.getFullYear());
			} else {
				const startOfYear = new Date(date.getFullYear(), 0, 1);
				const dayOfYear = Math.floor((date.getTime() - startOfYear.getTime()) / 86400000);
				const weekNum = Math.ceil((dayOfYear + startOfYear.getDay() + 1) / 7);
				period = `${date.getFullYear()}-W${String(weekNum).padStart(2, "0")}`;
			}

			if (period !== opts.targetPeriod) continue;
			const prev = postMap.get(rec.post_id);
			if (!prev || new Date(rec.collected_at).getTime() >= new Date(prev.collected_at).getTime()) {
				postMap.set(rec.post_id, rec);
			}
		}

		const items: TimelinePeriodPostItem[] = [];
		for (const rec of postMap.values()) {
			const meta = this.postMetaMap.get(rec.post_id);
			const likes = rec.metrics.likes || 0;
			const comments = rec.metrics.comments || 0;
			const shares = rec.metrics.shares || 0;
			const score = this.calcScore(rec.metrics);
			items.push({
				postId: rec.post_id,
				watchId: meta?.watchId,
				fbPostId: meta?.fbPostId,
				vaultSlug: meta?.vaultSlug || rec.post_id,
				titleSnippet: meta?.titleSnippet || `Bài viết ${rec.post_id}`,
				authorName: meta?.authorName || rec.platform || "Facebook",
				sourceType: meta?.sourceType || "external",
				url: meta?.url || "",
				publishedAt: meta?.publishedAt,
				collectedAt: rec.collected_at,
				score,
				likes,
				comments,
				shares,
			});
		}

		return items.sort((a, b) => b.score - a.score);
	}

	// Phuong thuc tuong thich nguoc
	getTimeline(groupBy: "week" | "month", filterAudience?: string): TimelinePoint[] {
		return this.queryTimelineAdvanced({
			groupBy,
			days: 0,
			metric: "score",
			dateBasis: "collected",
			sourceFilter: "all",
			filterAudience,
		}).points;
	}

	// --- Nhom 10: Truy van Xep hang Da chieu (Bai viet / Nguon Trang / Tag / Audience / Pillar) ---

	public queryRankingAdvanced(opts: RankingQueryOptions): TagRankEntry[] {
		const recent = this.getLatestRecordsByPost(
			this.filterByDays(opts.days, opts.dateBasis || "collected", opts.startDate, opts.endDate)
		).filter(
			(r) =>
				this.matchesSourceFilter(r.post_id, opts.sourceFilter, opts.sourceFilters) &&
				this.matchesAudienceFilter(r.post_id, undefined, opts.filterAudiences)
		);

		const bucketMap = new Map<
			string,
			{
				sublabel?: string;
				url?: string;
				score: number;
				likes: number;
				comments: number;
				shares: number;
				posts: Set<string>;
			}
		>();

		const addBucket = (
			key: string,
			rec: EngagementRecord,
			score: number,
			sublabel?: string,
			url?: string
		) => {
			const existing = bucketMap.get(key) || {
				sublabel,
				url,
				score: 0,
				likes: 0,
				comments: 0,
				shares: 0,
				posts: new Set<string>(),
			};
			existing.score += score;
			existing.likes += rec.metrics.likes || 0;
			existing.comments += rec.metrics.comments || 0;
			existing.shares += rec.metrics.shares || 0;
			existing.posts.add(rec.post_id);
			bucketMap.set(key, existing);
		};

		for (const rec of recent) {
			const meta = this.postMetaMap.get(rec.post_id);
			const score = this.calcScore(rec.metrics);

			if (opts.dimension === "post") {
				const title = meta?.titleSnippet || `Bài viết ${rec.post_id}`;
				const author = meta?.authorName || rec.platform;
				addBucket(title, rec, score, author, meta?.url);
			} else if (opts.dimension === "author") {
				const author = meta?.authorName || ` Nguồn ${rec.platform}`;
				addBucket(author, rec, score);
			} else if (opts.dimension === "tag") {
				// Chi tinh cac bai viet DA LUU TRONG VAULT va da duoc gan tags trong YAML Frontmatter
				if (meta?.inVault && meta.tags.length > 0) {
					for (const t of meta.tags) {
						addBucket(t, rec, score);
					}
				}
			} else if (opts.dimension === "audience") {
				if (meta?.inVault && meta.audiences.length > 0) {
					for (const a of meta.audiences) {
						addBucket(a, rec, score);
					}
				}
			} else if (opts.dimension === "pillar") {
				if (meta?.inVault && meta.pillars.length > 0) {
					for (const p of meta.pillars) {
						addBucket(p, rec, score);
					}
				}
			}
		}

		const activeComp =
			opts.selectedMetrics && opts.selectedMetrics.length > 0
				? opts.selectedMetrics
				: (["likes", "comments", "shares"] as ComponentMetricKey[]);

		const entries: TagRankEntry[] = Array.from(bucketMap.entries()).map(([key, data]) => {
			const postCount = data.posts.size;
			const filteredLikes = activeComp.includes("likes") ? data.likes : 0;
			const filteredComments = activeComp.includes("comments") ? data.comments : 0;
			const filteredShares = activeComp.includes("shares") ? data.shares : 0;
			const customScore =
				filteredLikes * SCORE_WEIGHTS.likes +
				filteredComments * SCORE_WEIGHTS.comments +
				filteredShares * SCORE_WEIGHTS.shares;

			let val = customScore;
			if (opts.metric === "likes") val = data.likes;
			else if (opts.metric === "comments") val = data.comments;
			else if (opts.metric === "shares") val = data.shares;
			else if (opts.metric === "avg_score") val = postCount > 0 ? Math.round(customScore / postCount) : 0;

			return {
				tag: key,
				sublabel: data.sublabel,
				url: data.url,
				score: customScore,
				value: val,
				likes: filteredLikes,
				comments: filteredComments,
				shares: filteredShares,
				postCount,
			};
		});

		return entries.sort((a, b) => b.value - a.value).slice(0, opts.limit);
	}

	getTagRanking(limit: number = 15, days: number = 90): TagRankEntry[] {
		return this.queryRankingAdvanced({
			dimension: "tag",
			metric: "score",
			days,
			limit,
			sourceFilter: "all",
		});
	}

	// --- Nhom 11: Truy van trang thai & Sparkline 5 ngay cho tung bai viet ---

	/**
	 * Tinh chuoi 5 diem Score trong 5 ngay gan nhat (D-4 -> Hom nay) cho 1 bai viet.
	 * Nguyen tac trung thuc du lieu:
	 * - Ngay nao KHONG co du lieu quet cua bai viet do thi tra ve `null` ("Không có dữ liệu").
	 * - Tuyet doi khong tu dien (back-fill) diem hien tai vao cac ngay truoc khi bai viet chua duoc quet.
	 */
	public getPostScoreSparkline5Days(
		candidatePostIds: string[],
		currentScore: number,
		fallbackTimestampIso?: string
	): PostSparkline5D {
		const validIds = new Set(
			candidatePostIds.map((id) => String(id || "").trim()).filter((id) => id.length > 0)
		);
		const matching = this.records
			.filter((r) => validIds.has(r.post_id))
			.map((r) => ({
				ts: new Date(r.collected_at).getTime(),
				score: this.calcScore(r.metrics),
			}))
			.filter((x) => !isNaN(x.ts))
			.sort((a, b) => a.ts - b.ts);

		const now = new Date();
		const dayStarts: number[] = [];
		const dayEnds: number[] = [];
		const dayLabels: string[] = [];
		const pad = (n: number) => String(n).padStart(2, "0");

		for (let offset = 4; offset >= 0; offset--) {
			const d = new Date(now.getFullYear(), now.getMonth(), now.getDate() - offset);
			const startMs = new Date(d.getFullYear(), d.getMonth(), d.getDate(), 0, 0, 0, 0).getTime();
			const endMs = new Date(d.getFullYear(), d.getMonth(), d.getDate(), 23, 59, 59, 999).getTime();
			dayStarts.push(startMs);
			dayEnds.push(endMs);
			dayLabels.push(`${pad(d.getDate())}/${pad(d.getMonth() + 1)}`);
		}

		const dailyScores: Array<number | null> = [null, null, null, null, null];

		for (let i = 0; i < 5; i++) {
			const startMs = dayStarts[i];
			const endMs = dayEnds[i];
			let latestScoreOnDay: number | null = null;
			for (const rec of matching) {
				if (rec.ts >= startMs && rec.ts <= endMs) {
					latestScoreOnDay = rec.score;
				}
			}
			dailyScores[i] = latestScoreOnDay;
		}

		// Neu bai viet da duoc thu thap nhung chua co ban ghi trong file engagement JSONL (vi du bai cu phat hien tu timeline)
		// hoac vua quet hom nay, gan diem hien tai vao dung ngay thu thap thuc te (khong gan vao cac ngay truoc do)
		const anyRecordedIn5d = dailyScores.some((v) => v !== null);
		if (!anyRecordedIn5d) {
			const fallbackMs = fallbackTimestampIso ? new Date(fallbackTimestampIso).getTime() : Date.now();
			const targetMs = !isNaN(fallbackMs) && fallbackMs > 0 ? fallbackMs : Date.now();
			let placed = false;
			for (let i = 0; i < 5; i++) {
				if (targetMs >= dayStarts[i] && targetMs <= dayEnds[i]) {
					dailyScores[i] = currentScore;
					placed = true;
					break;
				}
			}
			if (!placed) {
				dailyScores[4] = currentScore;
			}
		} else if (dailyScores[4] !== null) {
			dailyScores[4] = currentScore;
		}

		const validScores = dailyScores.filter((v): v is number => v !== null);
		const validDaysCount = validScores.length;
		const totalScanCount = Math.max(1, matching.length);
		const isFirstScan = validDaysCount <= 1;
		const delta5d =
			validDaysCount >= 2 ? validScores[validScores.length - 1] - validScores[0] : null;

		return {
			dailyScores,
			dayLabels,
			delta5d,
			validDaysCount,
			totalScanCount,
			isFirstScan,
		};
	}

	getRecentRecords(limit: number = 5): EngagementRecord[] {
		return [...this.records]
			.sort((a, b) => new Date(b.collected_at).getTime() - new Date(a.collected_at).getTime())
			.slice(0, limit);
	}

	hasData(): boolean {
		return this.records.length > 0;
	}

	getRecordCount(): boolean | number {
		return this.records.length;
	}

	getIsInitialized(): boolean {
		return this.isInitialized;
	}
}
