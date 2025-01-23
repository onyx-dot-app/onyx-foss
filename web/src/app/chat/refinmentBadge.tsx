"use client";
import {
  Tooltip,
  TooltipTrigger,
  TooltipProvider,
  TooltipContent,
} from "@/components/ui/tooltip";
import { Button } from "@/components/ui/button";
import { FiChevronRight, FiGlobe } from "react-icons/fi";
import {
  StreamingPhase,
  StreamingPhaseText,
} from "./message/StreamingMessages";
import { SubQuestionDetail } from "./interfaces";
import { useEffect, useRef, useState } from "react";

const PHASES_ORDER: StreamingPhase[] = [
  StreamingPhase.WAITING,
  StreamingPhase.SUB_QUERIES,
  StreamingPhase.CONTEXT_DOCS,
  StreamingPhase.ANSWER,
  StreamingPhase.COMPLETE,
];

export function useOrderedPhases(externalPhase: StreamingPhase) {
  const [phaseQueue, setPhaseQueue] = useState<StreamingPhase[]>([]);
  const [displayedPhase, setDisplayedPhase] = useState<StreamingPhase>(
    StreamingPhase.WAITING
  );
  const lastDisplayTimestampRef = useRef<number>(Date.now());

  const getPhaseIndex = (phase: StreamingPhase) => {
    return PHASES_ORDER.indexOf(phase);
  };

  useEffect(() => {
    setPhaseQueue((prevQueue) => {
      const lastQueuedPhase =
        prevQueue.length > 0 ? prevQueue[prevQueue.length - 1] : displayedPhase;

      const lastQueuedIndex = getPhaseIndex(lastQueuedPhase);
      const externalIndex = getPhaseIndex(externalPhase);

      if (externalIndex <= lastQueuedIndex) {
        return prevQueue;
      }

      const missingPhases: StreamingPhase[] = [];
      for (let i = lastQueuedIndex + 1; i <= externalIndex; i++) {
        missingPhases.push(PHASES_ORDER[i]);
      }
      return [...prevQueue, ...missingPhases];
    });
  }, [externalPhase, displayedPhase]);

  useEffect(() => {
    if (phaseQueue.length === 0) return;
    let rafId: number;

    const processQueue = () => {
      const now = Date.now();
      const elapsed = now - lastDisplayTimestampRef.current;

      // Keep this at 1000ms from the original example (unchanged),
      // but you can adjust if you want a different visible time in *this* component.
      if (elapsed >= 1000) {
        setPhaseQueue((prevQueue) => {
          if (prevQueue.length > 0) {
            const [next, ...rest] = prevQueue;
            setDisplayedPhase(next);
            lastDisplayTimestampRef.current = Date.now();
            return rest;
          }
          return prevQueue;
        });
      }
      rafId = requestAnimationFrame(processQueue);
    };

    rafId = requestAnimationFrame(processQueue);
    return () => {
      if (rafId) {
        cancelAnimationFrame(rafId);
      }
    };
  }, [phaseQueue]);

  return StreamingPhaseText[displayedPhase];
}

export default function RefinemenetBadge({
  secondLevelSubquestions,
  toggleInitialAnswerVieinwg,
  isViewingInitialAnswer,
}: {
  secondLevelSubquestions?: SubQuestionDetail[] | null;
  toggleInitialAnswerVieinwg: () => void;
  isViewingInitialAnswer: boolean;
}) {
  const currentState = secondLevelSubquestions?.[0]
    ? secondLevelSubquestions[0].answer
      ? secondLevelSubquestions[0].is_complete
        ? StreamingPhase.COMPLETE
        : StreamingPhase.ANSWER
      : secondLevelSubquestions[0].context_docs
        ? StreamingPhase.CONTEXT_DOCS
        : secondLevelSubquestions[0].sub_queries
          ? StreamingPhase.SUB_QUERIES
          : secondLevelSubquestions[0].question
            ? StreamingPhase.WAITING
            : StreamingPhase.WAITING
    : StreamingPhase.WAITING;

  const message = useOrderedPhases(currentState);

  return (
    <TooltipProvider delayDuration={0}>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="flex loading-text items-center gap-x-2 text-black text-sm font-medium cursor-pointer hover:text-blue-600 transition-colors duration-200">
            Refining answer...
            <FiChevronRight
              className="inline-block text-text-darker"
              size={16}
            />
          </div>
        </TooltipTrigger>
        <TooltipContent className="w-80 p-4 bg-white shadow-lg rounded-md">
          <div className="space-y-4">
            <p className="text-lg leading-none font-semibold text-gray-800">
              {message}
            </p>
            <p className="text-sm text-gray-600">
              The answer is being refined based on additional context and
              analysis.
            </p>
            <Button
              onClick={() => toggleInitialAnswerVieinwg()}
              size="sm"
              className="w-full"
            >
              {isViewingInitialAnswer
                ? "See Live Updates"
                : "Hide Live Updates"}
              <FiGlobe className="inline-block mr-2" />
            </Button>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
