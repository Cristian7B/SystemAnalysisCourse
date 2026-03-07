import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { MapContainer, TileLayer, Marker, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { surplus as surplusApi } from '../api';
import toast from 'react-hot-toast';
import './Post.css';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
    iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
    shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const CATEGORIES = ['produce', 'bakery', 'dairy', 'prepared_food', 'canned_goods', 'beverages', 'frozen', 'other'];
const STEPS = ['Details', 'Location', 'Schedule', 'Review'];

function LocationPicker({ position, setPosition }) {
    useMapEvents({ click: (e) => setPosition([e.latlng.lat, e.latlng.lng]) });
    return position ? <Marker position={position} /> : null;
}

export default function Post() {
    const navigate = useNavigate();
    const [step, setStep] = useState(0);
    const [loading, setLoading] = useState(false);
    const [photos, setPhotos] = useState([]);
    const [form, setForm] = useState({
        title: '', description: '', category: 'produce',
        quantityKg: '', quantityDesc: '',
        locationLabel: '', exactLocation: false,
        lat: '', lng: '',
        pickupStart: '', pickupEnd: '', expiresAt: '',
    });
    const [pinPosition, setPinPosition] = useState(null);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        accept: { 'image/*': [] },
        maxFiles: 5,
        onDrop: useCallback(files => {
            setPhotos(prev => [...prev, ...files].slice(0, 5));
        }, []),
    });

    const set = (key, value) => setForm(f => ({ ...f, [key]: value }));

    const handleSubmit = async () => {
        if (!pinPosition) { toast.error('Please pick a location on the map'); return; }
        setLoading(true);
        try {
            const fd = new FormData();
            Object.entries({ ...form, lat: pinPosition[0], lng: pinPosition[1] }).forEach(([k, v]) => fd.append(k, v));
            photos.forEach(p => fd.append('photos', p));
            await surplusApi.create(fd);
            toast.success('Surplus item posted successfully! 🎉');
            navigate('/');
        } catch (err) {
            toast.error(err.response?.data?.error || 'Failed to post item');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="post-page">
            <div className="container">
                <div className="post-header">
                    <h1>Post Surplus Food</h1>
                    <p>Share what you have — every kilogram counts</p>
                </div>

                {/* Step indicator */}
                <div className="step-indicator">
                    {STEPS.map((s, i) => (
                        <div key={s} className={`step ${i === step ? 'active' : ''} ${i < step ? 'done' : ''}`}>
                            <div className="step-num">{i < step ? '✓' : i + 1}</div>
                            <span>{s}</span>
                        </div>
                    ))}
                </div>

                <div className="post-card card card-body">
                    {/* Step 0: Details */}
                    {step === 0 && (
                        <div className="animate-in">
                            <h3 className="mb-16">Food Details</h3>
                            <div className="form-group">
                                <label className="form-label">Title *</label>
                                <input className="form-input" placeholder="e.g. Fresh vegetables from restaurant" required
                                    value={form.title} onChange={e => set('title', e.target.value)} />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Description</label>
                                <textarea className="form-textarea" placeholder="Describe the food, condition, packaging..."
                                    value={form.description} onChange={e => set('description', e.target.value)} />
                            </div>
                            <div className="grid-2">
                                <div className="form-group">
                                    <label className="form-label">Category *</label>
                                    <select className="form-select" value={form.category} onChange={e => set('category', e.target.value)}>
                                        {CATEGORIES.map(c => <option key={c} value={c}>{c.replace('_', ' ')}</option>)}
                                    </select>
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Quantity (kg) *</label>
                                    <input type="number" className="form-input" min="0.1" step="0.1"
                                        value={form.quantityKg} onChange={e => set('quantityKg', e.target.value)} />
                                </div>
                            </div>
                            <div className="form-group">
                                <label className="form-label">Quantity description</label>
                                <input className="form-input" placeholder="e.g. 3 boxes of apples, ~2kg each"
                                    value={form.quantityDesc} onChange={e => set('quantityDesc', e.target.value)} />
                            </div>

                            {/* Photo upload */}
                            <div className="form-group">
                                <label className="form-label">Photos (up to 5)</label>
                                <div {...getRootProps()} className={`dropzone ${isDragActive ? 'active' : ''}`}>
                                    <input {...getInputProps()} />
                                    <span>📷 Drop photos here, or click to select</span>
                                </div>
                                {photos.length > 0 && (
                                    <div className="photo-previews">
                                        {photos.map((f, i) => (
                                            <div key={i} className="photo-thumb">
                                                <img src={URL.createObjectURL(f)} alt="" />
                                                <button onClick={() => setPhotos(p => p.filter((_, j) => j !== i))} className="photo-remove">✕</button>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Step 1: Location */}
                    {step === 1 && (
                        <div className="animate-in">
                            <h3 className="mb-16">Pickup Location</h3>
                            <div className="form-group">
                                <label className="form-label">Location label</label>
                                <input className="form-input" placeholder="e.g. Back entrance of Green Market, 5th Ave"
                                    value={form.locationLabel} onChange={e => set('locationLabel', e.target.value)} />
                            </div>
                            <div className="form-group">
                                <label className="form-label" style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                                    <input type="checkbox" checked={form.exactLocation} onChange={e => set('exactLocation', e.target.checked)} />
                                    Share exact location (otherwise approximate area shown)
                                </label>
                            </div>
                            <p className="text-muted mb-8">📍 Click on the map to place your pin</p>
                            <MapContainer center={[40.7128, -74.006]} zoom={13} style={{ height: 360, borderRadius: 12, border: '1px solid var(--border-color)' }}>
                                <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                                <LocationPicker position={pinPosition} setPosition={setPinPosition} />
                            </MapContainer>
                            {pinPosition && (
                                <p className="text-muted mt-8">📍 {pinPosition[0].toFixed(5)}, {pinPosition[1].toFixed(5)}</p>
                            )}
                        </div>
                    )}

                    {/* Step 2: Schedule */}
                    {step === 2 && (
                        <div className="animate-in">
                            <h3 className="mb-16">Pickup Schedule</h3>
                            <div className="grid-2">
                                <div className="form-group">
                                    <label className="form-label">Pickup window start *</label>
                                    <input type="datetime-local" className="form-input"
                                        value={form.pickupStart} onChange={e => set('pickupStart', e.target.value)} />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Pickup window end *</label>
                                    <input type="datetime-local" className="form-input"
                                        value={form.pickupEnd} onChange={e => set('pickupEnd', e.target.value)} />
                                </div>
                            </div>
                            <div className="form-group">
                                <label className="form-label">Item expires at *</label>
                                <input type="datetime-local" className="form-input"
                                    value={form.expiresAt} onChange={e => set('expiresAt', e.target.value)} />
                            </div>
                            <div className="info-box">
                                <strong>🕐 Priority Windows:</strong>
                                <ul>
                                    <li>Charities get exclusive access for the first 2 hours</li>
                                    <li>Trusted collectors join after charities</li>
                                    <li>Open to everyone after priority windows expire</li>
                                </ul>
                            </div>
                        </div>
                    )}

                    {/* Step 3: Review */}
                    {step === 3 && (
                        <div className="animate-in">
                            <h3 className="mb-16">Review & Post</h3>
                            <div className="review-grid">
                                <div className="review-item"><strong>Title</strong><span>{form.title}</span></div>
                                <div className="review-item"><strong>Category</strong><span>{form.category}</span></div>
                                <div className="review-item"><strong>Quantity</strong><span>{form.quantityKg}kg</span></div>
                                <div className="review-item"><strong>Location</strong><span>{form.locationLabel || (pinPosition ? `${pinPosition[0].toFixed(4)}, ${pinPosition[1].toFixed(4)}` : '—')}</span></div>
                                <div className="review-item"><strong>Pickup Start</strong><span>{form.pickupStart}</span></div>
                                <div className="review-item"><strong>Pickup End</strong><span>{form.pickupEnd}</span></div>
                                <div className="review-item"><strong>Expires</strong><span>{form.expiresAt}</span></div>
                                <div className="review-item"><strong>Photos</strong><span>{photos.length} selected</span></div>
                            </div>
                        </div>
                    )}

                    {/* Navigation */}
                    <div className="step-nav">
                        {step > 0 && (
                            <button className="btn btn-secondary" onClick={() => setStep(s => s - 1)}>← Back</button>
                        )}
                        {step < STEPS.length - 1 ? (
                            <button
                                className="btn btn-primary"
                                disabled={step === 0 && (!form.title || !form.quantityKg)}
                                onClick={() => setStep(s => s + 1)}
                            >
                                Next →
                            </button>
                        ) : (
                            <button className="btn btn-primary" onClick={handleSubmit} disabled={loading}>
                                {loading ? <span className="spinner" style={{ width: 18, height: 18 }} /> : '🚀 Publish Post'}
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
