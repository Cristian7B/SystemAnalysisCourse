import MapView from '../components/Map/MapView';
import './Home.css';

export default function Home() {
    return (
        <div className="home-page">
            <div className="home-hero">
                <div className="container">
                    <div className="hero-content">
                        <div className="hero-badge"><span>🌱</span> Fighting Food Waste Together</div>
                        <h1 className="hero-title">
                            Rescue Food.<br />
                            <span className="hero-highlight">Change Lives.</span>
                        </h1>
                        <p className="hero-sub">
                            Connect with local donors, charities, and recipients to ensure surplus food finds a home — not a landfill.
                        </p>
                    </div>
                    <div className="hero-stats">
                        <div className="stat-pill"><span className="stat-num">0kg</span><span className="stat-label">Redistributed</span></div>
                        <div className="stat-pill"><span className="stat-num">0</span><span className="stat-label">Successful Pickups</span></div>
                        <div className="stat-pill"><span className="stat-num">0</span><span className="stat-label">Active Donors</span></div>
                    </div>
                </div>
            </div>
            <div className="container map-section">
                <MapView />
            </div>
        </div>
    );
}
