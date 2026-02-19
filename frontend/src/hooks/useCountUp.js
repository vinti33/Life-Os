import { useState, useEffect } from 'react';

export const useCountUp = (end, duration = 1000) => {
    const [count, setCount] = useState(0);

    useEffect(() => {
        let startTime = null;
        const start = count; // Start from current count to animate transitions

        if (start === end) return;

        const animate = (timestamp) => {
            if (!startTime) startTime = timestamp;
            const progress = timestamp - startTime;
            const percentage = Math.min(progress / duration, 1);

            // Ease out quart
            const ease = 1 - Math.pow(1 - percentage, 4);

            const nextCount = Math.floor(start + (end - start) * ease);
            setCount(nextCount);

            if (progress < duration) {
                requestAnimationFrame(animate);
            } else {
                setCount(end);
            }
        };

        requestAnimationFrame(animate);
    }, [end, duration]); // Re-run when target changes

    return count;
};
