export const patterns = [
    {
        id: "two_pointer",
        name: "Two Pointer",
        description:
            "Solve array and string problems by maintaining two strategically placed pointers.",
        category: "Arrays & Strings",
        difficulty: "Medium",
        videoCount: 6,
        completedVideos: 0,
        mastery: 0,
        thumbnail:
            "https://img.youtube.com/vi/Fu7LD_mIo00/hqdefault.jpg",
        videos: [],
    },

    {
        id: "sliding-window",
        name: "Sliding Window",
        description:
            "Efficiently solve contiguous subarray and substring problems using a moving window.",
        category: "Arrays & Strings",
        difficulty: "Medium",
        videoCount: 0,
        completedVideos: 0,
        mastery: 0,
        thumbnail: "",
        videos: [],
    },

    {
        id: "binary-search",
        name: "Binary Search",
        description:
            "Search sorted or monotonic spaces efficiently by repeatedly eliminating half the possibilities.",
        category: "Searching",
        difficulty: "Medium",
        videoCount: 0,
        completedVideos: 0,
        mastery: 0,
        thumbnail: "",
        videos: [],
    },

    {
        id: "recursion",
        name: "Recursion",
        description:
            "Understand problems by breaking them into smaller self-similar subproblems.",
        category: "Fundamentals",
        difficulty: "Medium",
        videoCount: 0,
        completedVideos: 0,
        mastery: 0,
        thumbnail: "",
        videos: [],
    },

    {
        id: "linked-list",
        name: "Linked List",
        description:
            "Master pointer manipulation and structural transformations in linked lists.",
        category: "Data Structures",
        difficulty: "Medium",
        videoCount: 0,
        completedVideos: 0,
        mastery: 0,
        thumbnail: "",
        videos: [],
    },

    {
        id: "stack",
        name: "Stack",
        description:
            "Use LIFO-based reasoning to solve parsing, monotonicity and simulation problems.",
        category: "Data Structures",
        difficulty: "Medium",
        videoCount: 0,
        completedVideos: 0,
        mastery: 0,
        thumbnail: "",
        videos: [],
    },

    {
        id: "queue",
        name: "Queue",
        description:
            "Understand FIFO processing and its applications in traversal and scheduling.",
        category: "Data Structures",
        difficulty: "Easy",
        videoCount: 0,
        completedVideos: 0,
        mastery: 0,
        thumbnail: "",
        videos: [],
    },

    {
        id: "tree",
        name: "Binary Tree",
        description:
            "Build strong intuition around tree traversal, recursion and structural reasoning.",
        category: "Trees",
        difficulty: "Medium",
        videoCount: 0,
        completedVideos: 0,
        mastery: 0,
        thumbnail: "",
        videos: [],
    },

    {
        id: "bst",
        name: "Binary Search Tree",
        description:
            "Use ordering properties of BSTs to solve search, validation and optimization problems.",
        category: "Trees",
        difficulty: "Medium",
        videoCount: 0,
        completedVideos: 0,
        mastery: 0,
        thumbnail: "",
        videos: [],
    },

    {
        id: "heap",
        name: "Heap / Priority Queue",
        description:
            "Solve top-k, scheduling and dynamic minimum/maximum problems efficiently.",
        category: "Data Structures",
        difficulty: "Hard",
        videoCount: 0,
        completedVideos: 0,
        mastery: 0,
        thumbnail: "",
        videos: [],
    },

    {
        id: "graph",
        name: "Graph",
        description:
            "Develop strong intuition for graph traversal, connectivity and shortest paths.",
        category: "Graphs",
        difficulty: "Hard",
        videoCount: 0,
        completedVideos: 0,
        mastery: 0,
        thumbnail: "",
        videos: [],
    },

    {
        id: "dfs",
        name: "DFS",
        description:
            "Explore graph and tree structures deeply using recursive or iterative traversal.",
        category: "Graphs",
        difficulty: "Medium",
        videoCount: 0,
        completedVideos: 0,
        mastery: 0,
        thumbnail: "",
        videos: [],
    },

    {
        id: "bfs",
        name: "BFS",
        description:
            "Use level-by-level exploration for shortest path and state-space problems.",
        category: "Graphs",
        difficulty: "Medium",
        videoCount: 0,
        completedVideos: 0,
        mastery: 0,
        thumbnail: "",
        videos: [],
    },

    {
        id: "dynamic-programming",
        name: "Dynamic Programming",
        description:
            "Identify overlapping subproblems and optimal substructure to design efficient solutions.",
        category: "Optimization",
        difficulty: "Hard",
        videoCount: 0,
        completedVideos: 0,
        mastery: 0,
        thumbnail: "",
        videos: [],
    },

    {
        id: "backtracking",
        name: "Backtracking",
        description:
            "Explore decision spaces while pruning invalid or unnecessary branches.",
        category: "Recursion",
        difficulty: "Hard",
        videoCount: 0,
        completedVideos: 0,
        mastery: 0,
        thumbnail: "",
        videos: [],
    },
];


export const PROJECT_STATS = {
    patterns: "20–25",
    videos: "128+",
    system: "AI Revision",
};


export function getPatternById(id) {

    if (!id) {
        return undefined;
    }

    const normalizedId =
        String(id)
            .trim()
            .toLowerCase()
            .replace(
                /_/g,
                "-"
            );

    return patterns.find(
        (pattern) =>
            String(pattern.id)
                .trim()
                .toLowerCase()
                .replace(
                    /_/g,
                    "-"
                ) === normalizedId
    );
}