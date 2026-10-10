/**
 * HomePage — landing page with two big cards: Detect / Predict.
 */

import { Link } from 'react-router-dom';

export function HomePage() {
  return (
    <main className="home" data-testid="home-page">
      <h1>Plagiarism_Detected</h1>
      <p className="home__sub">
        Two tools: detect similar passages against your reference corpus, and predict whether a
        document is human-written, AI-generated, or plagiarised.
      </p>
      <div className="home__cards">
        <Link to="/detect" className="home__card" data-testid="card-detect">
          <h2>Detect Plagiarism</h2>
          <p>Compare a document against your corpus using 4 algorithms.</p>
        </Link>
        <Link to="/predict" className="home__card" data-testid="card-predict">
          <h2>Predict Authenticity</h2>
          <p>3-class score: human / AI / plagiarised.</p>
        </Link>
        <Link to="/corpus" className="home__card" data-testid="card-corpus">
          <h2>Manage Corpus</h2>
          <p>Upload reference documents to your local index.</p>
        </Link>
        <Link to="/history" className="home__card" data-testid="card-history">
          <h2>History</h2>
          <p>Review past analyses stored on this device.</p>
        </Link>
      </div>
    </main>
  );
}
