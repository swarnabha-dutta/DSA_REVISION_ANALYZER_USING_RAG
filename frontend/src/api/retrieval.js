import { searchKnowledge } from "./client";

export async function searchDSA(query) {
    if (!query?.trim()) {
        return {
            results: [],
        };
    }

    return searchKnowledge(query.trim());
}

export function getBestVideoResult(results = []) {
    if (!results.length) return null;

    return [...results].sort((a, b) => {
        const scoreB = Number(b.score || 0);
        const scoreA = Number(a.score || 0);

        return scoreB - scoreA;
    })[0];
}