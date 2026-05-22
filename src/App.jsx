import { useMemo, useState } from 'react';

const whatItDoes = [
  {
    title: 'You bring your Snapchat download',
    body: 'Use the normal Snapchat data download. MemoryBridge does not need your Snapchat password.',
  },
  {
    title: 'It finds your memories',
    body: 'It looks inside the download for your photos, videos, and the list Snapchat includes with each memory.',
  },
  {
    title: 'It puts the dates and places back',
    body: 'If Snapchat included the real date or place, MemoryBridge matches that info to the right photo or video.',
  },
  {
    title: 'You get a clean folder',
    body: 'Your memories come out with readable names, correct dates, real places when available, and a simple receipt.',
  },
];

const steps = [
  { label: 'Download', detail: 'Get your data from Snapchat.' },
  { label: 'Drop it in', detail: 'Add the export to MemoryBridge.' },
  { label: 'Clean it up', detail: 'Dates and places are matched to files.' },
  { label: 'Keep it', detail: 'Save the clean folder wherever you want.' },
];

const faqs = [
  {
    question: 'What does MemoryBridge actually do?',
    answer:
      'It turns a messy Snapchat data download into a clean folder of photos and videos. It keeps the real dates and places Snapchat included, and it gives you a simple receipt showing what was found.',
  },
  {
    question: 'Where do the dates and places come from?',
    answer:
      'They come from a file Snapchat puts inside your download. That file lists each memory with its date, type, and place when Snapchat has one.',
  },
  {
    question: 'Does it guess where a memory was taken?',
    answer:
      'No. If Snapchat did not include a real place, MemoryBridge marks it as no place. It does not make up locations.',
  },
  {
    question: 'Why not just unzip the Snapchat download?',
    answer:
      'Because the photos and videos are separate from the list that explains them. MemoryBridge matches them back together so your memories are easier to keep and sort.',
  },
  {
    question: 'Does this log into my Snapchat?',
    answer:
      'No. You request your own Snapchat data first, then use MemoryBridge on that download. The app is not a Snapchat login tool.',
  },
  {
    question: 'What if some memories have no place?',
    answer:
      'That is normal. Some Snapchat exports say 0,0 instead of a real place. MemoryBridge treats that as blank and keeps the memory anyway.',
  },
  {
    question: 'What do I get at the end?',
    answer:
      'A cleaned folder with your photos and videos, names based on their dates, and a receipt file that says how many memories were cleaned.',
  },
];

const assetUrl = (path) => {
  const cleanPath = path.replace(/^\/+/, '');
  const base = typeof document === 'undefined' ? import.meta.env.BASE_URL : document.baseURI;
  return new URL(cleanPath, base).toString();
};

function locationStatus(value) {
  if (!value || typeof value !== 'string') return 'Missing';
  const matches = value.match(/-?\d+(?:\.\d+)?/g);
  if (!matches || matches.length < 2) return 'Missing';
  const lat = Number(matches[0]);
  const lon = Number(matches[1]);
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) return 'Invalid';
  if (Math.abs(lat) > 90 || Math.abs(lon) > 180) return 'Invalid';
  if (lat === 0 && lon === 0) return 'Blank';
  return 'Real';
}

function coerceItems(raw) {
  if (Array.isArray(raw)) return raw;
  if (Array.isArray(raw?.['Saved Media'])) return raw['Saved Media'];
  if (Array.isArray(raw?.savedMedia)) return raw.savedMedia;
  return [];
}

function summarize(items) {
  const withDate = items.filter((item) => item.Date || item.date).length;
  const withPlace = items.filter((item) => locationStatus(item.Location || item.location) === 'Real').length;
  const blankPlace = items.filter((item) => locationStatus(item.Location || item.location) === 'Blank').length;
  const videos = items.filter((item) => String(item['Media Type'] || item.type || '').toLowerCase().includes('video')).length;

  return {
    total: items.length,
    withDate,
    withPlace,
    blankPlace,
    videos,
    photos: Math.max(0, items.length - videos),
  };
}

function formatPercent(part, total) {
  if (!total) return '0%';
  return `${Math.round((part / total) * 100)}%`;
}

export default function App() {
  const [fileName, setFileName] = useState('');
  const [items, setItems] = useState([]);
  const [error, setError] = useState('');

  const summary = useMemo(() => summarize(items), [items]);
  const previewItems = useMemo(() => items.slice(0, 5), [items]);

  async function handleFile(event) {
    const file = event.target.files?.[0];
    setError('');
    setItems([]);
    setFileName(file?.name || '');
    if (!file) return;

    try {
      const text = await file.text();
      const parsed = JSON.parse(text);
      const nextItems = coerceItems(parsed);
      if (!nextItems.length) {
        setError('No memory list was found in this file.');
        return;
      }
      setItems(nextItems);
    } catch (readError) {
      setError(readError instanceof Error ? readError.message : 'Could not read this file.');
    }
  }

  return (
    <main>
      <nav className="siteNav" aria-label="Primary">
        <a className="brand" href="#top">MemoryBridge</a>
        <div className="navLinks">
          <a href="#does">What it does</a>
          <a href="#check">Check yours</a>
          <a href="#faq">FAQ</a>
        </div>
        <a className="navCta" href="#check">Check yours</a>
      </nav>

      <header className="hero" id="top" style={{ '--hero-image': `url("${assetUrl('hero-memory-archive.png')}")` }}>
        <div className="heroContent">
          <p className="eyebrow heroEyebrow">For Snapchat Memories</p>
          <h1>Get your memories out clean.</h1>
          <p className="heroCopy">
            Snapchat gives you a download. MemoryBridge turns it into a simple folder of photos and videos that are
            easier to keep.
          </p>
          <div className="heroActions">
            <a className="primaryAction" href="#does">See what it does</a>
          </div>
        </div>
      </header>

      <section className="introBand" id="does">
        <div>
          <p className="sectionLabel">What it does</p>
          <h2>Snapchat gives you a pile of files. MemoryBridge makes it make sense.</h2>
        </div>
        <p>
          Your Snapchat download has photos and videos in one place, and the dates and places in another place.
          MemoryBridge matches them together and gives you a clean folder.
        </p>
      </section>

      <section className="proofGrid" aria-label="MemoryBridge product pillars">
        {whatItDoes.map((point) => (
          <article className="proofCard" key={point.title}>
            <h3>{point.title}</h3>
            <p>{point.body}</p>
          </article>
        ))}
      </section>

      <section className="workflowBand" aria-label="MemoryBridge workflow">
        <img src={assetUrl('memory-flow.png')} alt="MemoryBridge export cleanup flow" />
        <div className="workflowCopy">
          <p className="sectionLabel">How it works</p>
          <h2>Four steps. No mystery.</h2>
          <div className="workflowRows">
            {steps.map((step, index) => (
              <div className="workflowRow" key={step.label}>
                <span>{String(index + 1).padStart(2, '0')}</span>
                <strong>{step.label}</strong>
                <p>{step.detail}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="simpleBand">
        <div className="sectionIntro">
          <p className="sectionLabel">The simple version</p>
          <h2>MemoryBridge does not invent anything.</h2>
          <p>
            If Snapchat included a date, MemoryBridge keeps it. If Snapchat included a real place, MemoryBridge keeps
            it. If Snapchat only included a blank place like 0,0, MemoryBridge leaves the place blank.
          </p>
        </div>
      </section>

      <section className="topbar" id="check">
        <div>
          <p className="eyebrow">Check yours</p>
          <h2>See what Snapchat included before cleaning the full download.</h2>
        </div>
      </section>

      <section className="workspace" aria-label="MemoryBridge checker">
        <div className="importPanel">
          <div className="panelHeader">
            <div>
              <p className="sectionLabel">Memory list</p>
              <h2>Choose the Snapchat memory list file</h2>
            </div>
            <span className={summary.total ? 'status ready' : 'status'}>{summary.total ? 'Found' : 'Waiting'}</span>
          </div>

          <label className="dropZone">
            <input type="file" accept=".json,application/json" onChange={handleFile} />
            <span className="dropIcon" aria-hidden="true">+</span>
            <span>
              <strong>{fileName || 'Choose memories_history.json'}</strong>
              <small>
                {summary.total ? `${summary.total.toLocaleString()} memories found` : 'This check runs in your browser'}
              </small>
            </span>
          </label>

          {error && <p className="errorText">{error}</p>}

          <div className="metrics" aria-label="Memory list numbers">
            <Metric label="Memories" value={summary.total.toLocaleString()} />
            <Metric label="With dates" value={formatPercent(summary.withDate, summary.total)} />
            <Metric label="With places" value={formatPercent(summary.withPlace, summary.total)} />
            <Metric label="Blank places" value={summary.blankPlace.toLocaleString()} />
            <Metric label="Videos" value={summary.videos.toLocaleString()} />
          </div>

          <div className="plainResult">
            <h3>What this means</h3>
            <p>
              The full cleaner uses this list to match your Snapchat photos and videos with their dates and places.
              This preview only checks the list file.
            </p>
          </div>
        </div>

        <aside className="auditPanel">
          <div className="panelHeader">
            <div>
              <p className="sectionLabel">Preview</p>
              <h2>First few memories</h2>
            </div>
          </div>

          <div className="coverageRows">
            <Coverage label="Photos" value={summary.photos} total={summary.total} />
            <Coverage label="Videos" value={summary.videos} total={summary.total} />
            <Coverage label="Real places" value={summary.withPlace} total={summary.total} />
            <Coverage label="Blank places" value={summary.blankPlace} total={summary.total} />
          </div>

          <div className="previewTable">
            <div className="tableHead">
              <span>Date</span>
              <span>Type</span>
              <span>Place</span>
            </div>
            {previewItems.length ? (
              previewItems.map((item, index) => {
                const placeStatus = locationStatus(item.Location || item.location);
                return (
                  <div className="tableRow" key={`${item.Date || item.date || 'row'}-${index}`}>
                    <span>{item.Date || item.date || 'Missing'}</span>
                    <span>{item['Media Type'] || item.type || 'Media'}</span>
                    <span>{placeStatus}</span>
                  </div>
                );
              })
            ) : (
              <div className="emptyState">No file checked yet.</div>
            )}
          </div>
        </aside>
      </section>

      <section className="faqBand" id="faq">
        <div className="sectionIntro">
          <p className="sectionLabel">FAQ</p>
          <h2>Plain answers.</h2>
        </div>
        <div className="faqList">
          {faqs.map((faq) => (
            <details key={faq.question}>
              <summary>{faq.question}</summary>
              <p>{faq.answer}</p>
            </details>
          ))}
        </div>
      </section>

      <footer className="footer">
        <strong>MemoryBridge</strong>
        <span>Keep the memories. Leave the mess.</span>
        <a href="#top">Back to top</a>
      </footer>
    </main>
  );
}

function Metric({ label, value }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function Coverage({ label, value, total }) {
  const percent = total ? Math.round((value / total) * 100) : 0;
  return (
    <div className="coverage">
      <div>
        <span>{label}</span>
        <strong>{value.toLocaleString()}</strong>
      </div>
      <div className="bar" aria-hidden="true">
        <span style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}
