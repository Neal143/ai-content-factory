/**
 * Ten file: EngagementStore.ts
 * Last update: 02/11/2026 17:35 (GMT+7)
 * Vai tro: Tang du lieu doc/ghi/truy van da chieu engagement tu file JSONL va bo dem Facebook Tracker trong vault.
 * Duoc su dung khi nao?: Khi plugin khoi dong, khi user nhap du lieu, khi cac view bieu do can truy van da chieu.
 * Output: Cac phuong thuc truy van engagement theo thoi gian (Ngay/Tuan/Thang), chi so (Score/Likes/Comments/Shares/Avg),
 *         nguon (Thuong hieu/Doi thu/Tung Trang), va xep hang da chieu (Bai viet, Nguon Trang, Tag/Hashtag, Audience, Pillar).
 * Tom tat logic hoat dong: Doc file JSONL trong .content-pipeline/engagement/, ket hop quet YAML frontmatter trong vault
 *          va du lieu thuc te tu .content-pipeline/fb-tracker-state.json + fb-watchlist.json de phan tich toan dien.
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
export type RankingDimension = "post" | "author" | "tag" | "audience" | "pillar";

export interface TimelineQueryOptions {
	groupBy: TimelineGroupBy;
	days: number; // 0 = Tat ca thoi gian (neu khong truyen startDate/endDate)
	startDate?: string; // YYYY-MM-DD
	endDate?: string; // YYYY-MM-DD
	metric: ChartMetricType;
	dateBasis: "published" | "collected";
	sourceFilter: string; // "all" | "own" | "external" | "author:<name>"
	filterAudience?: string;
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
	sourceType: "own" | "external";
	titleSnippet: string;
	url: string;
	publishedAt?: string; // ISO 8601
}

// Nhom 4: Lop EngagementStore
export class EngagementStore {
	private app: App;
	private tagIndex: TagIndex | null;
	private records: EngagementRecord[] = [];
	private postMetaMap: Map<string, PostMeta> = new Map();
	private knownAuthors: Set<string> = new Set();
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
			const sourceType: "own" | "external" =
				fm.source_type === "own" || normPath.startsWith("03-Content/Posted") ? "own" : "external";
			const publishedAt = fm.publish_date ? new Date(String(fm.publish_date)).toISOString() : undefined;

			const pillars = resolvePillars(audiences);
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
			};
			this.postMetaMap.set(postId, metaObj);
			if (hasFbPostId) {
				this.postMetaMap.set(String(fm.fb_post_id).trim(), metaObj);
			}
		}

		// 2. Bo sung thong tin Tieu de / Tac gia / Ngay dang tu fb-tracker-state.json (Khong tu tao tags/audience cho bai chua luu Vault)
		try {
			const wlPath = ".content-pipeline/fb-watchlist.json";
			const stPath = ".content-pipeline/fb-tracker-state.json";
			const watchSourceMap = new Map<string, { sourceType: "own" | "external"; url: string; fromPage?: string }>();

			if (await this.app.vault.adapter.exists(wlPath)) {
				const wl = JSON.parse(await this.app.vault.adapter.read(wlPath));
				for (const p of wl?.posts || []) {
					if (p?.id) {
						watchSourceMap.set(p.id, {
							sourceType: p.source_type === "own" ? "own" : "external",
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
						watchSourceMap.set(d.id, {
							sourceType: d.source_type === "own" ? "own" : "external",
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
					const sourceType: "own" | "external" =
						pState.source_type === "own" || wInfo?.sourceType === "own" ? "own" : "external";
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
						sourceType: existingMeta ? existingMeta.sourceType : sourceType,
						titleSnippet: snippet,
						url: wInfo?.url || existingMeta?.url || (fbId ? `https://www.facebook.com/${fbId}` : ""),
						publishedAt: publishedAt || existingMeta?.publishedAt,
					};

					if (slug) this.postMetaMap.set(slug, finalMeta);
					if (fbId) this.postMetaMap.set(fbId, finalMeta);
				}
			}
		} catch {
			// Bo qua neu file chua ton tai
		}
	}

	public getKnownAuthors(): string[] {
		return Array.from(this.knownAuthors).sort((a, b) => a.localeCompare(b));
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

	private matchesSourceFilter(postId: string, sourceFilter: string): boolean {
		if (!sourceFilter || sourceFilter === "all") return true;
		const meta = this.postMetaMap.get(postId);
		if (!meta) return sourceFilter === "external";
		if (sourceFilter === "own") return meta.sourceType === "own";
		if (sourceFilter === "external") return meta.sourceType === "external";
		if (sourceFilter.startsWith("author:")) {
			const targetAuthor = sourceFilter.slice(7);
			return meta.authorName === targetAuthor;
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
			if (!this.matchesSourceFilter(rec.post_id, opts.sourceFilter)) return false;
			if (opts.filterAudience) {
				const meta = this.postMetaMap.get(rec.post_id);
				if (!meta || !meta.audiences.includes(opts.filterAudience)) return false;
			}
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
		).filter((r) => this.matchesSourceFilter(r.post_id, opts.sourceFilter));

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

		const entries: TagRankEntry[] = Array.from(bucketMap.entries()).map(([key, data]) => {
			const postCount = data.posts.size;
			let val = data.score;
			if (opts.metric === "likes") val = data.likes;
			else if (opts.metric === "comments") val = data.comments;
			else if (opts.metric === "shares") val = data.shares;
			else if (opts.metric === "avg_score") val = postCount > 0 ? Math.round(data.score / postCount) : 0;

			return {
				tag: key,
				sublabel: data.sublabel,
				url: data.url,
				score: data.score,
				value: val,
				likes: data.likes,
				comments: data.comments,
				shares: data.shares,
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

	// --- Nhom 11: Truy van trang thai ---

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
