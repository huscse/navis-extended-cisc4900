'use client';

import { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';

export default function DynamicGreeting() {
  const greetings = useMemo(
    () => [
      {
        main: 'Vision & language',
        highlight: 'in sync',
        second: 'Search open-world',
        endHighlight: 'driving data.',
      },

      {
        main: 'Perception stack',
        highlight: 'awake',
        second: 'Explore the road,',
        endHighlight: 'frame by frame.',
      },
      {
        main: 'Navis core',
        highlight: 'initialized',
        second: 'Natural language meets',
        endHighlight: 'driving data.',
      },
      {
        main: 'Query-to-vision',
        highlight: 'engaged',
        second: 'Ask for concepts, objects, or',
        endHighlight: 'events.',
      },
    ],
    [],
  );

  const [g, setG] = useState(greetings[0]);

  useEffect(() => {
    setG(greetings[Math.floor(Math.random() * greetings.length)]);
  }, [greetings]);

  return (
    <div className="text-center">
      <motion.h1
        initial="hidden"
        animate="show"
        variants={{
          hidden: { opacity: 0, y: 8 },
          show: {
            opacity: 1,
            y: 0,
            transition: { duration: 0.9, ease: 'easeOut' },
          },
        }}
        className="text-3xl sm:text-4xl md:text-5xl font-extrabold tracking-tight leading-tight mb-15"
      >
        {/* Line 1 */}
        <motion.span
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.05 }}
        >
          {g.main}{' '}
          <span className="text-slate-300 font-extrabold">{g.highlight}</span>
        </motion.span>

        <br />

        {/* Line 2 */}
        <motion.span
          className="block"
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.25 }}
        >
          {g.second}{' '}
          <span className="text-slate-300 font-extrabold">
            {g.endHighlight}
          </span>
        </motion.span>
      </motion.h1>
    </div>
  );
}
