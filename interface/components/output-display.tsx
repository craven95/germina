'use client';

import React from 'react';

interface OutputDisplayProps {
  output: string;
}

export function OutputDisplay({ output }: OutputDisplayProps) {
  return (
    <div
      className="mt-4 w-full max-w-2xl bg-white p-4 rounded shadow"
      dangerouslySetInnerHTML={{ __html: output }}
    />
  );
}
