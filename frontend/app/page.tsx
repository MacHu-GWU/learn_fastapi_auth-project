import Link from 'next/link';

export default function Home() {
  return (
    <section className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
      <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
        Hello World!
      </h1>
      <p className="text-lg text-gray-600 mb-8">
        Welcome to FastAPI User Authentication Project
      </p>
      <div className="flex gap-4">
        <Link
          href="/signup"
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
        >
          Create Account
        </Link>
        <Link
          href="/signin"
          className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors font-medium"
        >
          Sign In
        </Link>
      </div>
    </section>
  );
}
