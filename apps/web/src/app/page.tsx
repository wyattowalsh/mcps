export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-4 py-8">
      <div className="text-center">
        <h1 className="text-5xl font-bold mb-4 text-[var(--primary)]">
          Welcome to MCPS
        </h1>
        <p className="text-xl text-gray-600 dark:text-gray-400 mb-8 max-w-2xl">
          A modern web application built with Next.js 15, React 19, and Tailwind CSS 4
        </p>

        <div className="flex gap-4 justify-center mb-12">
          <a
            href="#"
            className="btn-primary"
          >
            Get Started
          </a>
          <a
            href="#"
            className="px-4 py-2 border border-[var(--primary)] text-[var(--primary)] rounded-lg hover:bg-[var(--primary)] hover:text-white transition-colors"
          >
            Learn More
          </a>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl">
          <div className="p-6 rounded-lg border border-gray-200 dark:border-gray-800 hover:border-[var(--primary)] transition-colors">
            <h2 className="text-2xl font-semibold mb-2">Fast</h2>
            <p className="text-gray-600 dark:text-gray-400">
              Built with Next.js 15 for optimal performance
            </p>
          </div>
          <div className="p-6 rounded-lg border border-gray-200 dark:border-gray-800 hover:border-[var(--primary)] transition-colors">
            <h2 className="text-2xl font-semibold mb-2">Modern</h2>
            <p className="text-gray-600 dark:text-gray-400">
              Using React 19 with TypeScript for type safety
            </p>
          </div>
          <div className="p-6 rounded-lg border border-gray-200 dark:border-gray-800 hover:border-[var(--primary)] transition-colors">
            <h2 className="text-2xl font-semibold mb-2">Styled</h2>
            <p className="text-gray-600 dark:text-gray-400">
              Tailwind CSS 4 for beautiful and responsive design
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
