import { useMemo, useState } from 'react';

const providers = [
  { id: 'google_photos', name: 'Google Photos', state: 'Planned' },
  { id: 'onedrive', name: 'OneDrive', state: 'Planned' },
  { id: 'google_drive', name: 'Google Drive', state: 'Planned' },
  { id: 'dropbox', name: 'Dropbox', state: 'Later' },
];

const workflow = [
  { label: 'Import', detail: 'memories_history.json' },
  { label: 'Repair', detail: 'dates, GPS, sidecars' },
  { label: 'Upload', detail: 'chosen cloud' },
  { label: 'Audit', detail: 'proof of transfer' },
];

const metadataSteps = [
  {
    label: 'Date',
    source: 'memories_history.json → Date',
    output: 'filename, file modified time, JPEG DateTimeOriginal',
  },
  {
    label: 'Location',
    source: 'memories_history.json → Location',
    output: 'JPEG GPS tags when coordinates are real, sidecar always',
  },
  {
    label: 'Media type',
    source: 'memories_history.json → Media Type',
    output: 'photo/video matching against memories/*-main files',
  },
  {
    label: 'Raw proof',
    source: 'original Snapchat row',
    output: '.memorybridge.json sidecar plus run manifest',
  },
];

const productPoints = [
  {
    title: 'No Snapchat password',
    body: 'Users bring their official export. MemoryBridge never asks for account credentials.',
  },
  {
    title: 'Metadata repaired first',
    body: 'Dates, GPS coordinates, filenames, and sidecars are prepared before any upload starts.',
  },
  {
    title: 'Cloud choice stays open',
    body: 'Google Photos, OneDrive, Google Drive, and local archive support can share the same queue.',
  },
];

const pricing = [
  { name: 'Free audit', price: '$0', detail: 'Preview export coverage and download the local processor.' },
  { name: 'One-time rescue', price: '$19', detail: 'Repair one Snapchat export and back it up to one cloud.' },
  { name: 'Annual vault', price: '$39', detail: 'Run recurring exports, dedupe, and keep a verified archive.' },
];

const faqs = [
  {
    question: 'Where does the metadata come from?',
    answer: 'From Snapchat’s official memories_history.json file. Each row contains fields like Date, Media Type, and Location, and MemoryBridge maps those fields into timestamps, EXIF, filenames, and sidecars.',
  },
  {
    question: 'Can this pull directly from Snapchat?',
    answer: 'The product is built around user-provided Snapchat exports, not account scraping or password sharing.',
  },
  {
    question: 'Where does the media go?',
    answer: 'The local processor keeps files on the user machine until the user chooses a cloud destination.',
  },
  {
    question: 'What happens when metadata is missing?',
    answer: 'MemoryBridge preserves what the export contains and writes an audit sidecar for anything it cannot embed.',
  },
];

const assetUrl = (path) => `${import.meta.env.BASE_URL}${path.replace(/^\/+/, '')}`;

function locationStatus(value) {
  if (!value || typeof value !== 'string') return 'Missing';
  const matches = value.match(/-?\d+(?:\.\d+)?/g);
  if (!matches || matches.length < 2) return 'Missing';
  const lat = Number(matches[0]);
  const lon = Number(matches[1]);
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) return 'Invalid';
  if (Math.abs(lat) > 90 || Math.abs(lon) > 180) return 'Invalid';
  if (lat === 0 && lon === 0) return 'Placeholder';
  return 'Real';
}

function coerceItems(raw) {
  if (Array.isArray(raw)) return raw;
  if (Array.isArray(raw?.['Saved Media'])) return raw['Saved Media'];
  if (Array.isArray(raw?.savedMedia)) return raw.savedMedia;
  return [];
}

function summarize(items) {
  const withUrl = items.filter((item) => item['Media Download Url'] || item.downloadUrl).length;
  const withDate = items.filter((item) => item.Date || item.date).length;
  const withLocation = items.filter((item) => locationStatus(item.Location || item.location) === 'Real').length;
  const placeholderLocation = items.filter((item) => locationStatus(item.Location || item.location) === 'Placeholder').length;
  const videos = items.filter((item) => String(item['Media Type'] || item.type || '').toLowerCase().includes('video')).length;

  return {
    total: items.length,
    withUrl,
    withDate,
    withLocation,
    placeholderLocation,
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
  const [selectedProvider, setSelectedProvider] = useState('google_photos');

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
        setError('No Saved Media records were found in this JSON file.');
        return;
      }
      setItems(nextItems);
    } catch (readError) {
      setError(readError instanceof Error ? readError.message : 'Could not read this JSON file.');
    }
  }

  return (
    <main>
      <nav className="siteNav" aria-label="Primary">
        <a className="brand" href="#top">MemoryBridge</a>
        <div className="navLinks">
          <a href="#product">Product</a>
          <a href="#metadata">Metadata</a>
          <a href="#pricing">Pricing</a>
          <a href="#audit">Audit</a>
          <a href="#faq">FAQ</a>
        </div>
        <a className="navCta" href="#audit">Try audit</a>
      </nav>

      <header className="hero" id="top" style={{ '--hero-image': `url("${assetUrl('hero-memory-archive.png')}")` }}>
        <div className="heroContent">
          <p className="eyebrow heroEyebrow">Snap export backup</p>
          <h1>MemoryBridge</h1>
          <p className="heroCopy">
            Rescue Snapchat Memories exports into a clean camera roll with dates, locations, and cloud-ready files.
          </p>
          <div className="heroActions">
            <a className="primaryAction" href="#audit">Audit an export</a>
            <a className="secondaryAction" href="#processor">See processor</a>
          </div>
          <div className="heroProof" aria-label="Product proof points">
            <span>Snap export</span>
            <span>EXIF repair</span>
            <span>Cloud backup</span>
          </div>
        </div>
      </header>

      <section className="introBand" id="product">
        <div>
          <p className="sectionLabel">Product</p>
          <h2>For people ready to leave without abandoning years of photos and videos.</h2>
        </div>
        <p>
          Snapchat gives people the export. MemoryBridge makes that export useful: human filenames,
          restored timestamps, GPS where available, upload-ready files, and a transfer log.
        </p>
      </section>

      <section className="proofGrid" aria-label="MemoryBridge product pillars">
        {productPoints.map((point) => (
          <article className="proofCard" key={point.title}>
            <h3>{point.title}</h3>
            <p>{point.body}</p>
          </article>
        ))}
      </section>

      <section className="workflowBand" aria-label="MemoryBridge workflow">
        <img src={assetUrl('memory-flow.png')} alt="MemoryBridge export to cloud workflow" />
        <div className="workflowCopy">
          <p className="sectionLabel">Workflow</p>
          <h2>Export in. Repaired archive out.</h2>
          <div className="workflowRows">
            {workflow.map((step, index) => (
              <div className="workflowRow" key={step.label}>
                <span>{String(index + 1).padStart(2, '0')}</span>
                <strong>{step.label}</strong>
                <p>{step.detail}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="metadataBand" id="metadata">
        <div className="sectionIntro">
          <p className="sectionLabel">Metadata source</p>
          <h2>Nothing is guessed. The export JSON is the source of truth.</h2>
          <p>
            Snapchat ships each memory with a row in <code>memories_history.json</code>. MemoryBridge reads those
            rows, pairs them with the official <code>memories/*-main</code> media files, then writes the metadata
            into filenames, file timestamps, JPEG EXIF, and sidecars.
          </p>
        </div>
        <div className="metadataGrid">
          {metadataSteps.map((step) => (
            <article className="metadataCard" key={step.label}>
              <span>{step.label}</span>
              <strong>{step.source}</strong>
              <p>{step.output}</p>
            </article>
          ))}
        </div>
        <div className="metadataNote">
          <strong>About 0,0 GPS:</strong>
          <span>
            When Snapchat exports <code>Latitude, Longitude: 0.0, 0.0</code>, MemoryBridge preserves that raw value
            in the sidecar but does not write fake GPS into the image.
          </span>
        </div>
      </section>

      <section className="pricingBand" id="pricing">
        <div className="sectionIntro">
          <p className="sectionLabel">Pricing</p>
          <h2>Simple enough for a rescue job. Durable enough for a real product.</h2>
        </div>
        <div className="pricingGrid">
          {pricing.map((plan) => (
            <article className="priceCard" key={plan.name}>
              <h3>{plan.name}</h3>
              <strong>{plan.price}</strong>
              <p>{plan.detail}</p>
              <a href="#audit">Start</a>
            </article>
          ))}
        </div>
      </section>

      <section className="topbar" id="audit">
        <div>
          <p className="eyebrow">Live audit</p>
          <h2>Check a Snapchat export before you process anything.</h2>
        </div>
        <a className="downloadLink" href="#processor">Local processor</a>
      </section>

      <section className="workspace" aria-label="MemoryBridge workspace">
        <div className="importPanel">
          <div className="panelHeader">
            <div>
              <p className="sectionLabel">Import</p>
              <h2>Snapchat export audit</h2>
            </div>
            <span className={summary.total ? 'status ready' : 'status'}>{summary.total ? 'Ready' : 'Waiting'}</span>
          </div>

          <label className="dropZone">
            <input type="file" accept=".json,application/json" onChange={handleFile} />
            <span className="dropIcon" aria-hidden="true">+</span>
            <span>
              <strong>{fileName || 'Choose memories_history.json'}</strong>
              <small>{summary.total ? `${summary.total.toLocaleString()} records loaded` : 'Parsed locally in your browser'}</small>
            </span>
          </label>

          {error && <p className="errorText">{error}</p>}

          <div className="metrics" aria-label="Import metrics">
            <Metric label="Media" value={summary.total.toLocaleString()} />
            <Metric label="Dated" value={formatPercent(summary.withDate, summary.total)} />
            <Metric label="GPS" value={formatPercent(summary.withLocation, summary.total)} />
            <Metric label="0,0 GPS" value={summary.placeholderLocation.toLocaleString()} />
            <Metric label="URLs" value={formatPercent(summary.withUrl, summary.total)} />
          </div>

          <div className="split">
            <div>
              <p className="sectionLabel">Cloud target</p>
              <div className="providerList">
                {providers.map((provider) => (
                  <button
                    className={selectedProvider === provider.id ? 'provider active' : 'provider'}
                    key={provider.id}
                    onClick={() => setSelectedProvider(provider.id)}
                    type="button"
                  >
                    <span>{provider.name}</span>
                    <small>{provider.state}</small>
                  </button>
                ))}
              </div>
            </div>

            <div className="flowCard">
              <img src={assetUrl('memory-flow.png')} alt="MemoryBridge local export flow" />
              <div className="flowSteps">
                {workflow.map((step) => (
                  <div className="flowStep" key={step.label}>
                    <strong>{step.label}</strong>
                    <span>{step.detail}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        <aside className="auditPanel">
          <div className="panelHeader">
            <div>
              <p className="sectionLabel">Preview</p>
              <h2>Metadata coverage</h2>
            </div>
          </div>

          <div className="coverageRows">
            <Coverage label="Photo records" value={summary.photos} total={summary.total} />
            <Coverage label="Video records" value={summary.videos} total={summary.total} />
            <Coverage label="Real GPS records" value={summary.withLocation} total={summary.total} />
            <Coverage label="0,0 placeholders" value={summary.placeholderLocation} total={summary.total} />
            <Coverage label="Download links" value={summary.withUrl} total={summary.total} />
          </div>

          <div className="previewTable">
            <div className="tableHead">
              <span>Date</span>
              <span>Type</span>
              <span>GPS</span>
            </div>
            {previewItems.length ? (
              previewItems.map((item, index) => {
                const gpsStatus = locationStatus(item.Location || item.location);
                return (
                  <div className="tableRow" key={`${item.Date || item.date || 'row'}-${index}`}>
                    <span>{item.Date || item.date || 'Missing'}</span>
                    <span>{item['Media Type'] || item.type || 'Media'}</span>
                    <span>{gpsStatus}</span>
                  </div>
                );
              })
            ) : (
              <div className="emptyState">No export loaded.</div>
            )}
          </div>
        </aside>
      </section>

      <section className="processorBand" id="processor">
        <div>
          <p className="sectionLabel">Processor</p>
          <h2>Clean-room local engine</h2>
          <p>
            The Python tool can process a Snapchat export ZIP directly, scan connected Android public storage for
            export candidates, name files by capture time, write audit sidecars, write a run manifest, and embed JPEG
            metadata.
          </p>
        </div>
        <pre><code>cd memorybridge/processor{'\n'}python -m pip install -e .[exif]{'\n'}python -m memorybridge_export android-scan{'\n'}python -m memorybridge_export prepare-zip snapchat-export.zip --out cleaned</code></pre>
      </section>

      <section className="faqBand" id="faq">
        <div className="sectionIntro">
          <p className="sectionLabel">FAQ</p>
          <h2>The sharp edges, answered plainly.</h2>
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
        <span>Take the archive with you.</span>
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
