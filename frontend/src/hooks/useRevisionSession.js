import { useCallback, useState } from "react";

const INITIAL_STATE = {
    active: false,
    videoId: null,
    patternId: null,
    phase: "idle",
    questions: [],
    currentQuestion: 0,
    answers: [],
    evaluation: null,
    problems: [],
    resources: [],
    mastery: null,
};

export default function useRevisionSession() {
    const [session, setSession] = useState(INITIAL_STATE);

    const startRevision = useCallback(({ videoId, patternId }) => {
        setSession({
            ...INITIAL_STATE,
            active: true,
            videoId,
            patternId,
            phase: "questions",
        });
    }, []);

    const submitAnswer = useCallback((answer) => {
        setSession((previous) => ({
            ...previous,
            answers: [...previous.answers, answer],
        }));
    }, []);

    const setQuestions = useCallback((questions) => {
        setSession((previous) => ({
            ...previous,
            questions,
        }));
    }, []);

    const setEvaluation = useCallback((evaluation) => {
        setSession((previous) => ({
            ...previous,
            evaluation,
            phase: "problems",
        }));
    }, []);

    const setProblems = useCallback((problems) => {
        setSession((previous) => ({
            ...previous,
            problems,
            phase: "complete",
        }));
    }, []);

    const setResources = useCallback((resources) => {
        setSession((previous) => ({
            ...previous,
            resources,
        }));
    }, []);

    const setMastery = useCallback((mastery) => {
        setSession((previous) => ({
            ...previous,
            mastery,
        }));
    }, []);

    const closeRevision = useCallback(() => {
        setSession(INITIAL_STATE);
    }, []);

    return {
        session,
        startRevision,
        submitAnswer,
        setQuestions,
        setEvaluation,
        setProblems,
        setResources,
        setMastery,
        closeRevision,
    };
}