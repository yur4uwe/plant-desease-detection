import { ReportEngine } from "./report_engine.js";
import { readFileSync, existsSync } from "fs";
import { join } from "path";

const engine = new ReportEngine();

// process.argv contains: [node_path, script_path, arg1, arg2, ...]
const args = process.argv.slice(2);

// Should be ran from the report_creation/ directory
async function run() {
    if (args.length === 0) {
        console.log("Please specify step numbers as arguments (e.g., node src/generate_reports.js 6 7 8)");
        return;
    }

    if (!existsSync("reports")) {
        console.error("Please run this script from the report_creation/ directory");
        return;
    }

    for (const step of args) {
        try {
            const filePath = join("reports", `${step}.json`);
            const config = JSON.parse(readFileSync(filePath, "utf8"));
            await engine.generate(config, "./built_reports/");
        } catch (error) {
            console.error(`Error processing step ${step}:`, error.message);
        }
    }
}

run().catch(console.error);
