import {
    useEffect,
    useState,
} from "react";

import {
    useParams,
} from "react-router-dom";

import AIChat from "../components/ai/AIChat";
import ConceptQuestions from "../components/ai/ConceptQuestions";
import MasteryScore from "../components/ai/MasteryScore";

import ProblemSet from "../components/revision/ProblemSet";
import ResourceLinks from "../components/revision/ResourceLinks";

import {
    evaluateRevisionAnswer,
    generateRevisionQuestions,
    generatePracticeProblems,
    getLearningResources,
    getVideo,
} from "../api/client";

export default function Revision() {
    const {
        videoId,
    } = useParams();

    const [
        video,
        setVideo,
    ] = useState(null);

    const [
        questions,
        setQuestions,
    ] = useState([]);

    const [
        problems,
        setProblems,
    ] = useState([]);

    const [
        resources,
        setResources,
    ] = useState([]);

    const [
        evaluation,
        setEvaluation,
    ] = useState(null);

    const [
        messages,
        setMessages,
    ] = useState([]);

    const [
        loading,
        setLoading,
    ] = useState(true);

    const [
        evaluating,
        setEvaluating,
    ] = useState(false);

    useEffect(() => {
        async function initializeRevision() {
            try {
                setLoading(true);

                const videoResponse =
                    await getVideo(videoId);

                const loadedVideo =
                    videoResponse?.video;

                setVideo(
                    loadedVideo
                );

                const questionResponse =
                    await generateRevisionQuestions({
                        videoId,
                        patternId:
                            loadedVideo?.patternId,
                        language: "bn",
                        questionCount: 5,
                    });

                setQuestions(
                    questionResponse?.questions ||
                    []
                );

                const resourceResponse =
                    await getLearningResources({
                        videoId,
                        patternId:
                            loadedVideo?.patternId,
                    });

                setResources(
                    resourceResponse?.resources ||
                    []
                );

            } catch (error) {
                console.error(
                    "Revision initialization failed:",
                    error
                );

            } finally {
                setLoading(false);
            }
        }

        initializeRevision();
    }, [videoId]);

    async function handleAnswer(answer) {
        try {
            setEvaluating(true);

            const response =
                await evaluateRevisionAnswer({
                    videoId,
                    questionId:
                        answer.questionId,
                    answer:
                        answer.answer,
                    language: "bn",
                });

            setEvaluation(
                response
            );

            setMessages(
                (previous) => [
                    ...previous,
                    {
                        role: "user",
                        content:
                            answer.answer,
                    },
                    {
                        role: "assistant",
                        content:
                            response?.feedback ||
                            "তোমার উত্তর evaluate করা হয়েছে।",
                    },
                ]
            );

            const problemResponse =
                await generatePracticeProblems({
                    videoId,
                    patternId:
                        video?.patternId,
                    count: 5,
                    excludeKnownProblems: true,
                });

            setProblems(
                problemResponse?.problems ||
                []
            );

        } catch (error) {
            console.error(
                "Answer evaluation failed:",
                error
            );

        } finally {
            setEvaluating(false);
        }
    }

    function handleChatMessage(message) {
        setMessages(
            (previous) => [
                ...previous,
                {
                    role: "user",
                    content: message,
                },
            ]
        );
    }

    if (loading) {
        return (
            <main className="page-content">

                <div className="loading-card">
                    AI revision session তৈরি হচ্ছে...
                </div>

            </main>
        );
    }

    return (
        <main className="revision-page">

            <header className="revision-header">

                <span className="hero-eyebrow">
                    VIDEO COMPLETE · AI REVISION
                </span>

                <h1>
                    এখন বুঝে দেখি।
                </h1>

                <p>
                    {video?.title}
                </p>

            </header>

            <div className="revision-grid">

                <div className="revision-main">

                    <ConceptQuestions
                        questions={questions}
                        onSubmit={handleAnswer}
                        loading={evaluating}
                    />

                    {evaluation && (
                        <MasteryScore
                            score={
                                evaluation.masteryScore
                            }
                            label={
                                `${video?.patternName ||
                                "Concept"
                                } Mastery`
                            }
                        />
                    )}

                    <ResourceLinks
                        resources={resources}
                    />

                    <ProblemSet
                        problems={problems}
                    />

                </div>

                <AIChat
                    video={video}
                    pattern={{
                        name:
                            video?.patternName,
                    }}
                    messages={messages}
                    onSend={
                        handleChatMessage
                    }
                    onClose={() => { }}
                />

            </div>

        </main>
    );
}