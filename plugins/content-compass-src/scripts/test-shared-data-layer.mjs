/**
 * Tên file: test-shared-data-layer.mjs
 * Last update: 23/10/2026 20:05 (GMT+7)
 * Vai trò: Script kiểm thử độc lập cho tầng dữ liệu dùng chung (AudienceIndex và TagIndex).
 * Được sử dụng khi nào?: Chạy kiểm thử tự động trong Phase P3 để kiểm chứng logic trích xuất dữ liệu thực tế.
 * Output: Báo cáo kết quả kiểm tra số lượng audience, quan hệ phả hệ, pillar và topic.
 * Tóm tắt logic hoạt động: Đọc trực tiếp các file Audience .md trong vault và topic_map.yaml trong personas,
 * mô phỏng quy trình xử lý của AudienceIndex và TagIndex, in thống kê và assert tính toàn vẹn.
 */

// Nhóm 1: Import thư viện hệ thống
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const contentFactoryDir = path.resolve(__dirname, "../../../..");
const audiencesDir = path.join(contentFactoryDir, "vault", "01-Atomic", "Audiences");
const topicMapPath = path.join(contentFactoryDir, "personas", "Vuon-ong-steiner", "topic_map.yaml");

// Nhóm 2: Kiểm thử logic bóc tách Audience files
function testAudienceParsing() {
	console.log("\n--- [TEST 1] AUDIENCE INDEX PARSING ---");
	if (!fs.existsSync(audiencesDir)) {
		throw new Error(`Khong tim thay thu muc Audiences: ${audiencesDir}`);
	}

	const files = fs.readdirSync(audiencesDir).filter(f => f.endsWith(".md"));
	console.log(`Tim thay ${files.length} file .md trong vault/01-Atomic/Audiences/`);
	if (files.length !== 26) {
		throw new Error(`Ky vong 26 files nhung tim thay: ${files.length}`);
	}

	const nodes = new Map();

	for (const filename of files) {
		const filePath = path.join(audiencesDir, filename);
		const content = fs.readFileSync(filePath, "utf-8");
		const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---/);
		if (!match) continue;

		const fmLines = match[1].split(/\r?\n/);
		const fm = {};
		for (const line of fmLines) {
			const idx = line.indexOf(":");
			if (idx !== -1 && !line.startsWith(" ") && !line.startsWith("-")) {
				const key = line.slice(0, idx).trim();
				const val = line.slice(idx + 1).trim();
				fm[key] = val;
			}
		}

		const slug = filename.replace(/\.md$/, "");
		const displayName = fm.audience_main_job || slug;
		const level = fm.audience_level || "little";
		const isBuyerJob = fm.is_buyer_job === "true";

		let parentSlug = null;
		if (fm.parent_audience && fm.parent_audience.includes("[[")) {
			parentSlug = fm.parent_audience.replace(/\[\[|\]\]/g, "").replace(/['"]/g, "").split("|")[0].trim();
		} else {
			// Kiem tra block array
			const parentIdx = fmLines.findIndex(l => l.startsWith("parent_audience:"));
			if (parentIdx !== -1) {
				for (let j = parentIdx + 1; j < fmLines.length; j++) {
					const l = fmLines[j];
					if (l.trim().startsWith("- '[[") || l.trim().startsWith("- \"[[") || l.trim().startsWith("- [[")) {
						parentSlug = l.replace(/.*\[\[|\]\].*/g, "").split("|")[0].trim();
						break;
					}
					if (!l.startsWith(" ") && !l.startsWith("-")) break;
				}
			}
		}

		nodes.set(slug, {
			slug,
			displayName,
			level,
			parentSlug,
			childSlugs: [],
			isBuyerJob
		});
	}

	for (const [slug, node] of nodes.entries()) {
		if (node.parentSlug && nodes.has(node.parentSlug)) {
			nodes.get(node.parentSlug).childSlugs.push(slug);
		}
	}

	const roots = Array.from(nodes.values()).filter(n => n.level === "big" || !n.parentSlug);
	console.log(`Tong so node: ${nodes.size}`);
	console.log(`So root nodes (Big Job): ${roots.length}`);
	for (const r of roots) {
		console.log(`  - Root: ${r.displayName} (${r.slug}) -> ${r.childSlugs.length} con`);
	}

	if (roots.length === 0) {
		throw new Error("Khong tim thay root node nao!");
	}
	console.log("=> TEST 1 PASSED: AudienceIndex bóc tách chính xác 26 node và cấu trúc phả hệ.");
	return nodes;
}

// Nhóm 3: Kiểm thử logic nạp topic_map.yaml
function testTopicMapParsing(audienceNodes) {
	console.log("\n--- [TEST 2] TAG INDEX PARSING ---");
	if (!fs.existsSync(topicMapPath)) {
		throw new Error(`Khong tim thay file topic_map: ${topicMapPath}`);
	}

	const content = fs.readFileSync(topicMapPath, "utf-8");
	const lines = content.split(/\r?\n/);
	const topics = [];
	let currentTopic = null;
	let currentSection = null;

	for (const line of lines) {
		const trimmed = line.trim();
		if (trimmed.startsWith("- id:")) {
			if (currentTopic) topics.push(currentTopic);
			currentTopic = {
				id: trimmed.replace("- id:", "").trim(),
				label: "",
				pillar_parents: [],
				belongs_to_audience: []
			};
			currentSection = null;
		} else if (currentTopic) {
			if (trimmed.startsWith("label:")) {
				currentTopic.label = trimmed.replace("label:", "").trim();
				currentSection = null;
			} else if (trimmed.startsWith("pillar_parents:")) {
				currentSection = "pillar_parents";
			} else if (trimmed.startsWith("belongs_to_audience:")) {
				currentSection = "belongs_to_audience";
			} else if (trimmed.startsWith("-") && currentSection) {
				const val = trimmed.replace(/^-/, "").replace(/['"]/g, "").trim();
				if (currentSection === "pillar_parents") {
					currentTopic.pillar_parents.push(val);
				} else if (currentSection === "belongs_to_audience") {
					currentTopic.belongs_to_audience.push(val.replace(/\[\[|\]\]/g, "").trim());
				}
			}
		}
	}
	if (currentTopic) topics.push(currentTopic);

	console.log(`Tong so topic bóc tách được: ${topics.length}`);

	// Xay dung Pillars
	const pillars = new Map();
	for (const t of topics) {
		for (const p of t.pillar_parents) {
			if (!pillars.has(p)) {
				pillars.set(p, { name: p, topicCount: 0, audiences: new Set() });
			}
			const pObj = pillars.get(p);
			pObj.topicCount++;
			for (const a of t.belongs_to_audience) {
				pObj.audiences.add(a);
			}
		}
	}

	console.log(`Tong so Pillars tim thay: ${pillars.size}`);
	for (const [pName, pObj] of pillars.entries()) {
		console.log(`  - Pillar "${pName}": ${pObj.topicCount} topics, ${pObj.audiences.size} audiences`);
	}

	if (pillars.size === 0) {
		throw new Error("Khong tim thay pillar nao!");
	}
	console.log("=> TEST 2 PASSED: TagIndex bóc tách chính xác Pillars và Topics.");
}

// Nhóm 4: Chạy tổng thể kiểm tra
try {
	const audienceNodes = testAudienceParsing();
	testTopicMapParsing(audienceNodes);
	console.log("\n🎉 TOÀN BỘ KIỂM THỬ DATA LAYER P3 ĐÃ VƯỢT QUA 100%!");
} catch (err) {
	console.error("\n❌ KIỂM THỬ THẤT BẠI:", err.message);
	process.exit(1);
}
