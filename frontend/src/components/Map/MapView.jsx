import { useState, useEffect, useCallback, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import MarkerClusterGroup from 'react-leaflet-cluster';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { surplus as surplusApi } from '../../api';
import { useAuth } from '../../contexts/AuthContext';
import ClaimButton from '../Claims/ClaimButton';
import './MapView.css';

// Fix Leaflet default marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
    iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
    shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const CATEGORY_COLORS = {
    produce: '#22c55e',
    bakery: '#f59e0b',
    dairy: '#3b82f6',
    prepared_food: '#8b5cf6',
    canned_goods: '#06b6d4',
    beverages: '#ec4899',
    frozen: '#60a5fa',
    other: '#94a3b8',
};

const CATEGORY_EMOJI = {
    produce: '🥦', bakery: '🍞', dairy: '🥛', prepared_food: '🍽️',
    canned_goods: '🥫', beverages: '🧃', frozen: '🧊', other: '📦',
};

const createCustomIcon = (category, status) => {
    const color = status === 'available' ? (CATEGORY_COLORS[category] || '#22c55e') : '#64748b';
    const emoji = CATEGORY_EMOJI[category] || '📦';
    return L.divIcon({
        html: `
      <div style="
        background:${color};
        width:36px;height:36px;
        border-radius:50% 50% 50% 0;
        transform:rotate(-45deg);
        border:3px solid rgba(255,255,255,0.3);
        box-shadow:0 4px 12px rgba(0,0,0,0.4);
        display:flex;align-items:center;justify-content:center;
      ">
        <span style="transform:rotate(45deg);font-size:16px">${emoji}</span>
      </div>`,
        className: '',
        iconSize: [36, 36],
        iconAnchor: [18, 36],
        popupAnchor: [0, -40],
    });
};

// Component to re-center map
function MapController({ center }) {
    const map = useMap();
    useEffect(() => {
        if (center) map.setView(center, map.getZoom());
    }, [center, map]);
    return null;
}

const CATEGORIES = ['all', 'produce', 'bakery', 'dairy', 'prepared_food', 'canned_goods', 'beverages', 'frozen', 'other'];
const RADII = [2, 5, 10, 20, 50];

export default function MapView({ onSelectItem }) {
    const { user } = useAuth();
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(false);
    const [filters, setFilters] = useState({ category: 'all', radius: 10 });
    const [userLocation, setUserLocation] = useState(null);
    const [mapCenter, setMapCenter] = useState([40.7128, -74.006]); // NYC default

    const loadItems = useCallback(async () => {
        setLoading(true);
        try {
            const params = { limit: 200 };
            if (filters.category !== 'all') params.category = filters.category;
            if (userLocation) {
                params.lat = userLocation[0];
                params.lng = userLocation[1];
                params.radius = filters.radius;
            }
            const { data } = await surplusApi.list(params);
            setItems(data.items);
        } catch (err) {
            console.error('Failed to load surplus items', err);
        } finally {
            setLoading(false);
        }
    }, [filters, userLocation]);

    useEffect(() => { loadItems(); }, [loadItems]);

    useEffect(() => {
        navigator.geolocation?.getCurrentPosition(
            ({ coords }) => {
                setUserLocation([coords.latitude, coords.longitude]);
                setMapCenter([coords.latitude, coords.longitude]);
            },
            () => { }
        );
    }, []);

    const getWindowStatus = (item) => {
        const now = new Date();
        const charityEnd = new Date(item.charity_window_end);
        const trustedEnd = new Date(item.trusted_window_end);
        if (now < charityEnd) return { label: 'Charity Priority', cls: 'badge-blue' };
        if (now < trustedEnd) return { label: 'Trusted Priority', cls: 'badge-amber' };
        return { label: 'Open to All', cls: 'badge-green' };
    };

    return (
        <div className="map-wrapper">
            {/* Filter bar */}
            <div className="map-filters">
                <div className="filter-group">
                    <span className="filter-label">Category</span>
                    <div className="filter-pills">
                        {CATEGORIES.map(cat => (
                            <button
                                key={cat}
                                className={`filter-pill ${filters.category === cat ? 'active' : ''}`}
                                onClick={() => setFilters(f => ({ ...f, category: cat }))}
                            >
                                {cat === 'all' ? '🌍 All' : `${CATEGORY_EMOJI[cat]} ${cat.replace('_', ' ')}`}
                            </button>
                        ))}
                    </div>
                </div>
                <div className="filter-group">
                    <span className="filter-label">Radius: {filters.radius}km</span>
                    <div className="filter-pills">
                        {RADII.map(r => (
                            <button
                                key={r}
                                className={`filter-pill ${filters.radius === r ? 'active' : ''}`}
                                onClick={() => setFilters(f => ({ ...f, radius: r }))}
                            >
                                {r}km
                            </button>
                        ))}
                    </div>
                </div>
                <div className="map-stats">
                    {loading
                        ? <span className="pulse text-muted">Loading...</span>
                        : <span className="text-muted">{items.length} item{items.length !== 1 ? 's' : ''} found</span>}
                </div>
            </div>

            {/* Map */}
            <MapContainer
                center={mapCenter}
                zoom={13}
                className="leaflet-map"
                zoomControl={true}
            >
                <MapController center={mapCenter} />
                <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                />
                <MarkerClusterGroup
                    chunkedLoading
                    maxClusterRadius={60}
                    showCoverageOnHover={false}
                >
                    {items.map(item => (
                        <Marker
                            key={item.id}
                            position={[item.lat, item.lng]}
                            icon={createCustomIcon(item.category, item.status)}
                        >
                            <Popup maxWidth={320} minWidth={280}>
                                <div className="map-popup">
                                    {item.photos?.length > 0 && (
                                        <img className="popup-photo" src={item.photos[0]} alt={item.title} />
                                    )}
                                    <div className="popup-body">
                                        <div className="popup-header">
                                            <h3 className="popup-title">{item.title}</h3>
                                            <span className={`badge ${getWindowStatus(item).cls}`}>
                                                {getWindowStatus(item).label}
                                            </span>
                                        </div>
                                        <div className="popup-meta">
                                            <span>{CATEGORY_EMOJI[item.category]} {item.category?.replace('_', ' ')}</span>
                                            <span>⚖️ {item.quantity_kg}kg</span>
                                        </div>
                                        {item.description && (
                                            <p className="popup-desc">{item.description.slice(0, 100)}{item.description.length > 100 ? '…' : ''}</p>
                                        )}
                                        <div className="popup-footer">
                                            <div className="popup-donor">
                                                <span className="popup-donor-name">by {item.donor_name}</span>
                                                <span className={`badge badge-gray`}>🌱 {item.donor_badge}</span>
                                            </div>
                                            {user
                                                ? <ClaimButton item={item} onSuccess={loadItems} />
                                                : <a href="/login" className="btn btn-primary btn-sm">Sign in to claim</a>
                                            }
                                        </div>
                                    </div>
                                </div>
                            </Popup>
                        </Marker>
                    ))}
                </MarkerClusterGroup>

                {/* User location marker */}
                {userLocation && (
                    <Marker
                        position={userLocation}
                        icon={L.divIcon({
                            html: '<div style="width:14px;height:14px;background:#3b82f6;border-radius:50%;border:3px solid #fff;box-shadow:0 0 12px rgba(59,130,246,0.6)"></div>',
                            className: '',
                            iconSize: [14, 14],
                            iconAnchor: [7, 7],
                        })}
                    />
                )}
            </MapContainer>
        </div>
    );
}
