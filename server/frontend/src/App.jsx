import { useEffect, useState } from "react";
import { Link, Navigate, Route, Routes, useNavigate, useParams } from "react-router-dom";

import { apiGet, apiPost } from "./api.js";
import Register from "./components/Register/Register.jsx";

function Navbar({ user, onLogout }) {
  return (
    <header className="site-header">
      <nav className="nav-shell" aria-label="Main navigation">
        <Link className="brand" to="/" aria-label="Car Dealership Capstone home">
          <img src="/static/project-logo.svg" alt="" width="42" height="42" />
          <span>Roadside</span>
        </Link>
        <div className="nav-links">
          <Link to="/">Dealers</Link>
          <Link to="/cars">Makes &amp; Models</Link>
          <a href="/static/About.html">About Us</a>
          <a href="/static/Contact.html">Contact Us</a>
        </div>
        <div className="account-links">
          {user ? (
            <>
              <span className="signed-in" aria-label={"Signed in as " + user.username}>{user.username}</span>
              <button className="button button-small button-quiet" onClick={onLogout} type="button">Log out</button>
            </>
          ) : (
            <>
              <Link to="/login">Log in</Link>
              <Link className="button button-small button-outline" to="/register">Register</Link>
            </>
          )}
        </div>
      </nav>
    </header>
  );
}

function Notice({ children, kind = "info" }) {
  return <p className={"notice notice-" + kind} role={kind === "error" ? "alert" : "status"}>{children}</p>;
}

function DealerCard({ dealer, user }) {
  return (
    <article className="dealer-card">
      <div className="dealer-card-top">
        <span className="dealer-kicker">{dealer.city || dealer.state}</span>
        <span className="source-tag">Capstone record</span>
      </div>
      <h2><Link to={"/dealers/" + dealer.id}>{dealer.name}</Link></h2>
      <dl className="dealer-facts">
        <div><dt>ID</dt><dd>{dealer.id}</dd></div>
        <div><dt>City</dt><dd>{dealer.city || "Not listed"}</dd></div>
        <div><dt>State</dt><dd>{dealer.state || "Not listed"}</dd></div>
        <div><dt>Address</dt><dd>{dealer.address || "Not listed"}</dd></div>
        <div><dt>ZIP code</dt><dd>{dealer.zip || "Not listed"}</dd></div>
      </dl>
      {dealer.phone && <p><a href={"tel:" + dealer.phone}>{dealer.phone}</a></p>}
      <div className="card-actions">
        <Link className="text-link" to={"/dealers/" + dealer.id}>Details and reviews <span aria-hidden="true">→</span></Link>
        {user ? (
          <Link className="button button-primary button-small" to={"/dealers/" + dealer.id + "/review"}>Review Dealer</Link>
        ) : (
          <Link className="button button-outline button-small" to="/login">Sign in to review</Link>
        )}
      </div>
    </article>
  );
}

function HomePage({ user }) {
  const routeParams = useParams();
  const navigate = useNavigate();
  const [state, setState] = useState(routeParams.state || "");
  const [dealers, setDealers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadDealers(filter = "") {
    setLoading(true);
    setError("");
    try {
      const query = filter ? "?state=" + encodeURIComponent(filter) : "";
      setDealers(await apiGet("get_dealers" + query));
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const filter = routeParams.state || "";
    setState(filter);
    loadDealers(filter);
  }, [routeParams.state]);

  function applyFilter(event) {
    event.preventDefault();
    const value = state.trim();
    navigate(value ? "/dealers/state/" + encodeURIComponent(value) : "/");
  }

  const apiEndpoint = "/djangoapp/get_dealers" + (state.trim() ? "?state=" + encodeURIComponent(state.trim()) : "");

  return (
    <main>
      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">Find your next stop</p>
          <h1>Local dealers.<br /><em>Real experiences.</em></h1>
          <p className="hero-lede">Browse dealership details, explore customer reviews, and discover vehicle makes and models.</p>
          <a className="button button-light" href="#dealer-list">Explore dealers <span aria-hidden="true">↓</span></a>
        </div>
        <div className="hero-art" aria-hidden="true">
          <div className="sun-orbit" />
          <img src="/static/project-logo.svg" alt="" />
          <span className="art-label">Kansas &amp; beyond</span>
        </div>
      </section>
      <section className="section-wrap" id="dealer-list">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Directory</p>
            <h2>Dealerships</h2>
          </div>
          <form className="filter-form" onSubmit={applyFilter}>
            <label htmlFor="state-filter">Filter by state</label>
            <div className="filter-row">
              <input id="state-filter" value={state} onChange={(event) => setState(event.target.value)} placeholder="e.g. Kansas or KS" />
              <button className="button button-primary" type="submit">Filter</button>
              {state && <button className="button button-quiet" type="button" onClick={() => { setState(""); navigate("/"); }}>Clear</button>}
            </div>
            <a className="endpoint-link" href={apiEndpoint}>Open this API endpoint</a>
          </form>
        </div>
        {loading && <Notice>Loading dealership records…</Notice>}
        {error && <Notice kind="error">{error}</Notice>}
        {!loading && !error && dealers.length === 0 && (
          <div className="empty-state">
            <h3>No dealership records loaded yet</h3>
            <p>Load the official capstone dealer records from the backend folder with <code>python manage.py seed_course_data</code>.</p>
          </div>
        )}
        {!loading && !error && dealers.length > 0 && (
          <>
            <p className="result-count">{dealers.length} {dealers.length === 1 ? "dealer" : "dealers"}{state ? " in " + state : ""}</p>
            <div className="dealer-grid">{dealers.map((dealer) => <DealerCard key={dealer.id} dealer={dealer} user={user} />)}</div>
          </>
        )}
      </section>
    </main>
  );
}

function LoginPage({ onLogin }) {
  const [form, setForm] = useState({ username: "", password: "" });
  const [error, setError] = useState("");
  const navigate = useNavigate();

  async function submit(event) {
    event.preventDefault();
    setError("");
    try {
      await onLogin(form);
      navigate("/");
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  return (
    <section className="form-card">
      <p className="eyebrow">Welcome back</p>
      <h1>Log in</h1>
      <form onSubmit={submit}>
        <label>Username<input autoComplete="username" name="username" value={form.username} onChange={(event) => setForm({ ...form, username: event.target.value })} required /></label>
        <label>Password<input autoComplete="current-password" type="password" name="password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} required /></label>
        {error && <p className="form-message error" role="alert">{error}</p>}
        <button className="button button-primary" type="submit">Log in</button>
      </form>
      <p className="muted">New here? <Link to="/register">Create an account</Link>.</p>
    </section>
  );
}

function DealerPage({ user }) {
  const { dealerId } = useParams();
  const [dealer, setDealer] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    Promise.all([apiGet("get_dealers/" + dealerId), apiGet("get_reviews?dealerId=" + dealerId)])
      .then(([dealerData, reviewData]) => {
        if (active) {
          setDealer(dealerData);
          setReviews(reviewData);
        }
      })
      .catch((requestError) => active && setError(requestError.message));
    return () => { active = false; };
  }, [dealerId]);

  if (error) return <main className="section-wrap"><Notice kind="error">{error}</Notice><Link to="/">Back to dealers</Link></main>;
  if (!dealer) return <main className="section-wrap"><Notice>Loading dealer details…</Notice></main>;

  return (
    <main className="section-wrap detail-layout">
      <Link className="back-link" to="/">← All dealers</Link>
      <section className="detail-card">
        <p className="eyebrow">{dealer.city ? dealer.city + ", " + dealer.state : dealer.state}</p>
        <h1>{dealer.name}</h1>
        <dl className="dealer-facts dealer-facts-detail">
          <div><dt>ID</dt><dd>{dealer.id}</dd></div>
          <div><dt>City</dt><dd>{dealer.city}</dd></div>
          <div><dt>State</dt><dd>{dealer.state}</dd></div>
          <div><dt>Address</dt><dd>{dealer.address}</dd></div>
          <div><dt>ZIP code</dt><dd>{dealer.zip}</dd></div>
        </dl>
        {dealer.phone && <p>Phone: <a href={"tel:" + dealer.phone}>{dealer.phone}</a></p>}
        {dealer.website && <p>Website: <a href={dealer.website} target="_blank" rel="noreferrer">{dealer.website}</a></p>}
        <p className="source-note">Dealership record from the Full Stack Developer Capstone dataset.</p>
        <a className="endpoint-link" href={"/djangoapp/get_dealers/" + dealer.id}>Open dealer API endpoint</a>
        {user ? (
          <Link className="button button-primary" to={"/dealers/" + dealer.id + "/review"}>Review Dealer</Link>
        ) : (
          <Link className="button button-outline" to="/login">Log in to review</Link>
        )}
      </section>
      <section className="reviews-section">
        <div className="section-heading">
          <div><p className="eyebrow">Customer voices</p><h2>Reviews</h2></div>
          <a className="endpoint-link" href={"/djangoapp/get_reviews?dealerId=" + dealer.id}>Open reviews API endpoint</a>
        </div>
        {reviews.length === 0 ? <div className="empty-state"><p>No reviews have been posted for this dealer yet.</p></div> : (
          <div className="review-list">
            {reviews.map((review) => (
              <article className="review-card" key={review.id}>
                <div className="review-header">
                  <div className={"sentiment-badge sentiment-" + (review.sentiment || "neutral")}>
                    <img className="sentiment-image" src={"/static/sentiment-" + (review.sentiment || "neutral") + ".svg"} alt={(review.sentiment || "neutral") + " sentiment"} width="56" height="56" />
                    <span>{(review.sentiment || "neutral").replace(/^./, (letter) => letter.toUpperCase())}</span>
                  </div>
                  <p className="review-byline">{review.author} · {new Date(review.created_at).toLocaleDateString()}</p>
                </div>
                <p className="review-quote">“{review.text}”</p>
                {(review.purchase_date || review.car_make) && <p className="review-vehicle">{[review.car_make, review.car_model, review.car_year].filter(Boolean).join(" ")}{review.purchase_date ? " · Purchase date: " + review.purchase_date : ""}</p>}
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}

function ReviewPage({ user }) {
  const { dealerId } = useParams();
  const [dealer, setDealer] = useState(null);
  const [carModels, setCarModels] = useState([]);
  const [form, setForm] = useState({
    review: "",
    purchase: false,
    purchase_date: "",
    car_make: "",
    car_model: "",
    car_year: "",
  });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([apiGet("get_dealers/" + dealerId), apiGet("get_cars")])
      .then(([dealerData, carData]) => {
        setDealer(dealerData);
        setCarModels(carData.CarModels || []);
      })
      .catch((requestError) => setError(requestError.message));
  }, [dealerId]);

  if (!user) return <Navigate to="/login" replace />;
  const makes = [...new Set(carModels.map((car) => car.CarMake))];
  const models = carModels.filter((car) => car.CarMake === form.car_make).map((car) => car.CarModel);

  async function submit(event) {
    event.preventDefault();
    setError("");
    setSaving(true);
    try {
      await apiPost("add_review", {
        dealer_id: Number(dealerId),
        name: [user.first_name, user.last_name].filter(Boolean).join(" ") || user.username,
        ...form,
        car_year: form.car_year ? Number(form.car_year) : null,
      });
      navigate("/dealers/" + dealerId);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="form-card review-form-card">
      <p className="eyebrow">Share your experience</p>
      <h1>Post Review</h1>
      <p className="muted">{dealer ? "Your review for " + dealer.name + " will be public." : "Loading dealership…"}</p>
      <p className="endpoint-link">POST /djangoapp/add_review</p>
      <form onSubmit={submit}>
        <label htmlFor="review-text">Review</label>
        <textarea id="review-text" name="review" value={form.review} onChange={(event) => setForm({ ...form, review: event.target.value })} required minLength={5} maxLength={2000} rows={6} />
        <span className="field-hint">5–2,000 characters. Please keep the review respectful and based on your experience.</span>
        <label htmlFor="review-purchase-date">Purchase date<input id="review-purchase-date" type="date" value={form.purchase_date} onChange={(event) => setForm({ ...form, purchase_date: event.target.value })} /></label>
        <label className="checkbox-label"><input type="checkbox" checked={form.purchase} onChange={(event) => setForm({ ...form, purchase: event.target.checked })} /> I purchased a vehicle from this dealer</label>
        <div className="form-grid">
          <label htmlFor="review-car-make">Car make<select id="review-car-make" value={form.car_make} onChange={(event) => setForm({ ...form, car_make: event.target.value, car_model: "" })}><option value="">Select a make</option>{makes.map((make) => <option key={make} value={make}>{make}</option>)}</select></label>
          <label htmlFor="review-car-model">Car model<select id="review-car-model" value={form.car_model} onChange={(event) => setForm({ ...form, car_model: event.target.value })} disabled={!form.car_make}><option value="">Select a model</option>{models.map((model) => <option key={model} value={model}>{model}</option>)}</select></label>
          <label className="full-width" htmlFor="review-car-year">Car year<input id="review-car-year" type="number" min="1900" max="2035" value={form.car_year} onChange={(event) => setForm({ ...form, car_year: event.target.value })} /></label>
        </div>
        {error && <p className="form-message error" role="alert">{error}</p>}
        <button className="button button-primary" type="submit" disabled={saving || !dealer}>{saving ? "Submitting…" : "Post Review"}</button>
      </form>
    </section>
  );
}

function CarsPage() {
  const [catalog, setCatalog] = useState(null);
  const [models, setModels] = useState({});
  const [error, setError] = useState("");

  useEffect(() => {
    apiGet("get_cars").then(setCatalog).catch((requestError) => setError(requestError.message));
  }, []);

  async function loadModels(make) {
    try {
      const data = await apiGet("get_cars?makeId=" + make.MakeId);
      setModels((current) => ({ ...current, [make.MakeId]: data.models || [] }));
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  return (
    <main className="section-wrap">
      <p className="eyebrow">Course vehicle catalog</p>
      <h1>Car makes and models</h1>
      <p className="muted">Browse the car makes and models supplied with the capstone dataset.</p>
      {error && <Notice kind="error">{error}</Notice>}
      {!catalog && !error && <Notice>Loading the live vehicle catalogue…</Notice>}
      {catalog && (
        <div className="make-grid">
          {catalog.makes.map((make) => (
            <article className="make-card" key={make.MakeId}>
              <button type="button" className="make-button" onClick={() => loadModels(make)} aria-expanded={Boolean(models[make.MakeId])}>
                <span>{make.MakeName}</span><span aria-hidden="true">+</span>
              </button>
              {models[make.MakeId] && <ul>{models[make.MakeId].map((model) => <li key={model.Model_ID}>{model.Model_Name}</li>)}</ul>}
            </article>
          ))}
        </div>
      )}
      {catalog && <a className="endpoint-link" href="/djangoapp/get_cars">Open all makes API endpoint</a>}
    </main>
  );
}

export default function App() {
  const [user, setUser] = useState(null);
  const [sessionLoaded, setSessionLoaded] = useState(false);
  const [sessionError, setSessionError] = useState("");

  useEffect(() => {
    apiGet("session")
      .then((data) => setUser(data.user))
      .catch((requestError) => setSessionError(requestError.message))
      .finally(() => setSessionLoaded(true));
  }, []);

  async function handleLogin(credentials) {
    const data = await apiPost("login", credentials);
    setUser(data.user);
  }

  async function handleLogout() {
    try {
      await apiPost("logout");
      setUser(null);
    } catch (requestError) {
      setSessionError(requestError.message);
    }
  }

  if (!sessionLoaded) return <div className="loading-screen">Loading the dealership directory…</div>;

  return (
    <>
      <Navbar user={user} onLogout={handleLogout} />
      {sessionError && <div className="session-alert"><Notice kind="error">{sessionError}</Notice></div>}
      <Routes>
        <Route path="/" element={<HomePage user={user} />} />
        <Route path="/dealers/state/:state" element={<HomePage user={user} />} />
        <Route path="/register" element={<Register onRegistered={() => {}} />} />
        <Route path="/login" element={<LoginPage onLogin={handleLogin} />} />
        <Route path="/dealers/:dealerId" element={<DealerPage user={user} />} />
        <Route path="/dealers/:dealerId/review" element={<ReviewPage user={user} />} />
        <Route path="/cars" element={<CarsPage />} />
        <Route path="*" element={<main className="section-wrap"><h1>Page not found</h1><Link to="/">Return home</Link></main>} />
      </Routes>
      <footer className="site-footer">
        <p>Car Dealership Capstone</p>
        <span>Dealership, review, and vehicle sample records from the capstone dataset.</span>
      <a href="https://github.com/nguyenbao140506-debug/xrwvm-fullstack_developer_capstone">Project repository</a>
      </footer>
    </>
  );
}
