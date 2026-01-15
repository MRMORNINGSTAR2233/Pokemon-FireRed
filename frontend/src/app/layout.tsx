import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
    title: 'AI Pokemon Player',
    description: 'Autonomous AI system playing Pokemon FireRed using CrewAI and Groq',
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en">
            <body>{children}</body>
        </html>
    );
}
