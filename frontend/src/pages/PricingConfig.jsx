import { useState, useEffect } from 'react';
import { apiJson } from '../api';
import { useToast } from '../components/Toast';

export default function PricingConfig() {
  const showToast = useToast();
  const [dbBasePrice, setDbBasePrice] = useState(100);
  const [dbPricePerGb, setDbPricePerGb] = useState(50);
  const [dbTiers, setDbTiers] = useState([]);
  const [runsBasePrice, setRunsBasePrice] = useState(200);
  const [runsPricePerRun, setRunsPricePerRun] = useState(100);
  const [runsMinRuns, setRunsMinRuns] = useState(10);
  const [runsDiscountPercent, setRunsDiscountPercent] = useState(10);
  const [deployInhouse, setDeployInhouse] = useState(500);
  const [deployClient, setDeployClient] = useState(1000);
  const [whereBasePrice, setWhereBasePrice] = useState(300);
  const [birtComplexity, setBirtComplexity] = useState({});
  const [maximoBasePrice, setMaximoBasePrice] = useState(0);
  const [maximoPricePerFeature, setMaximoPricePerFeature] = useState(0);
  const [addonDb2, setAddonDb2] = useState(500);
  const [addonBirt, setAddonBirt] = useState(500);
  const [addonMaximo, setAddonMaximo] = useState(500);

  useEffect(() => { loadPricingConfig(); }, []);

  async function loadPricingConfig() {
    try {
      const configs = await apiJson('/api/pricing-config');
      if (configs.database_size_pricing) {
        const db = configs.database_size_pricing.value;
        setDbBasePrice(db.base_price || 100);
        setDbPricePerGb(db.price_per_gb || 50);
        if (db.tiers?.length) setDbTiers(db.tiers.map((t, i) => ({ ...t, id: i })));
      }
      if (configs.runs_pricing) {
        const runs = configs.runs_pricing.value;
        setRunsBasePrice(runs.base_price || 200);
        setRunsPricePerRun(runs.price_per_run || 100);
        if (runs.bulk_discount) {
          setRunsMinRuns(runs.bulk_discount.min_runs || 10);
          setRunsDiscountPercent(runs.bulk_discount.discount_percent || 10);
        }
      }
      if (configs.deployment_pricing) {
        const d = configs.deployment_pricing.value;
        setDeployInhouse(d.inhouse_vm || 500);
        setDeployClient(d.client_premises || 1000);
      }
      if (configs.where_clauses_pricing) setWhereBasePrice(configs.where_clauses_pricing.value.base_price || 300);
      if (configs.birt_reports_pricing?.value?.complexity_pricing) {
        const cp = {};
        for (let i = 0; i <= 5; i++) {
          const c = configs.birt_reports_pricing.value.complexity_pricing[i.toString()] || {};
          cp[i] = { price_per_report: c.price_per_report || 0, description: c.description || '' };
        }
        setBirtComplexity(cp);
      } else {
        const desc = ['No conversion needed', 'Minimal effort', 'Simple conversion', 'Moderate effort', 'Complex conversion', 'Very complex'];
        const cp = {};
        for (let i = 0; i <= 5; i++) cp[i] = { price_per_report: 0, description: desc[i] };
        setBirtComplexity(cp);
      }
      if (configs.maximo_upgrade_pricing) {
        setMaximoBasePrice(configs.maximo_upgrade_pricing.value.base_price || 0);
        setMaximoPricePerFeature(configs.maximo_upgrade_pricing.value.price_per_feature || 0);
      }
      if (configs.addon_installation_pricing) {
        const a = configs.addon_installation_pricing.value;
        setAddonDb2(a.db2_installation || 500);
        setAddonBirt(a.birt_installation || 500);
        setAddonMaximo(a.maximo_installation || 500);
      }
    } catch (err) {
      showToast('Error loading pricing configuration: ' + err.message, 'error');
    }
  }

  function addDbTier() {
    setDbTiers(t => [...t, { id: Date.now(), max_gb: null, price_per_gb: 0 }]);
  }

  function removeDbTier(id) {
    setDbTiers(t => t.filter(tier => tier.id !== id));
  }

  function updateDbTier(id, field, value) {
    setDbTiers(t => t.map(tier => tier.id === id ? { ...tier, [field]: value } : tier));
  }

  function updateBirtComp(level, field, value) {
    setBirtComplexity(prev => ({ ...prev, [level]: { ...prev[level], [field]: value } }));
  }

  async function saveAllPricing() {
    try {
      const pricing = {
        database_size_pricing: { base_price: dbBasePrice, price_per_gb: dbPricePerGb, tiers: dbTiers.filter(t => t.price_per_gb > 0).map(t => ({ max_gb: t.max_gb ? parseFloat(t.max_gb) : null, price_per_gb: parseFloat(t.price_per_gb) })) },
        runs_pricing: { base_price: runsBasePrice, price_per_run: runsPricePerRun, bulk_discount: { min_runs: runsMinRuns, discount_percent: runsDiscountPercent } },
        deployment_pricing: { inhouse_vm: deployInhouse, client_premises: deployClient },
        where_clauses_pricing: { base_price: whereBasePrice },
        birt_reports_pricing: { base_price: 0, complexity_pricing: {} },
        maximo_upgrade_pricing: { base_price: maximoBasePrice, price_per_feature: maximoPricePerFeature },
        addon_installation_pricing: { db2_installation: addonDb2, birt_installation: addonBirt, maximo_installation: addonMaximo },
      };

      for (let i = 0; i <= 5; i++) {
        if (birtComplexity[i]) {
          pricing.birt_reports_pricing.complexity_pricing[i.toString()] = {
            price_per_report: parseFloat(birtComplexity[i].price_per_report) || 0,
            description: birtComplexity[i].description || '',
          };
        }
      }

      const configs = [
        { key: 'database_size_pricing', value: pricing.database_size_pricing, desc: 'Pricing based on database size in GB' },
        { key: 'runs_pricing', value: pricing.runs_pricing, desc: 'Pricing for number of runs' },
        { key: 'deployment_pricing', value: pricing.deployment_pricing, desc: 'Pricing based on deployment type' },
        { key: 'where_clauses_pricing', value: pricing.where_clauses_pricing, desc: 'Additional pricing for WHERE clauses' },
        { key: 'birt_reports_pricing', value: pricing.birt_reports_pricing, desc: 'Complexity-based pricing for BIRT reports' },
        { key: 'maximo_upgrade_pricing', value: pricing.maximo_upgrade_pricing, desc: 'Pricing for Maximo upgrade features' },
        { key: 'addon_installation_pricing', value: pricing.addon_installation_pricing, desc: 'Pricing for Add-On Installation Services' },
      ];

      for (const config of configs) {
        const res = await fetch(`/api/pricing-config/${config.key}`, {
          method: 'PUT', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ value: config.value, description: config.desc }),
        });
        if (!res.ok) {
          const createRes = await fetch('/api/pricing-config', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ config_key: config.key, value: config.value, description: config.desc }),
          });
          if (!createRes.ok) throw new Error(`Failed to save ${config.key}`);
        }
      }
      showToast('✅ All pricing configuration saved successfully!', 'success');
    } catch (err) {
      showToast('❌ Error saving pricing: ' + err.message, 'error');
    }
  }

  const sectionStyle = { background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', boxShadow: 'var(--shadow-sm)', marginBottom: 20, overflow: 'hidden' };
  const headerStyle = { display: 'flex', alignItems: 'center', gap: 12, padding: '18px 24px', borderBottom: '1px solid var(--border)', background: 'var(--surface2)' };
  const bodyStyle = { padding: 24 };

  return (
    <div className="page medium">
      <div className="page-header">
        <h1>Pricing Configuration</h1>
        <p>Configure pricing tiers, BIRT complexity rates, and deployment costs.</p>
      </div>

      {/* Database Size Pricing */}
      <div style={sectionStyle}>
        <div style={headerStyle}>
          <div style={{ width: 4, height: 20, background: 'var(--accent)', borderRadius: 4 }} />
          <h2 style={{ fontSize: '1rem', fontWeight: 700, margin: 0 }}>Database Size Pricing</h2>
        </div>
        <div style={bodyStyle}>
          <div className="form-group"><label>Base Price ($)</label><input type="number" className="form-control" step="0.01" min="0" value={dbBasePrice} onChange={e => setDbBasePrice(parseFloat(e.target.value) || 0)} /></div>
          <div className="form-group"><label>Default Price per GB ($)</label><input type="number" className="form-control" step="0.01" min="0" value={dbPricePerGb} onChange={e => setDbPricePerGb(parseFloat(e.target.value) || 0)} /></div>
          <div style={{ marginTop: 14, padding: 16, background: 'var(--surface2)', borderRadius: 10, border: '1.5px solid var(--border)' }}>
            <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}><strong>Tiered Pricing (Optional)</strong></label>
            {dbTiers.map(tier => (
              <div key={tier.id} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: 10, marginBottom: 10, marginTop: 10, padding: 12, background: 'var(--surface)', borderRadius: 8, border: '1px solid var(--border)' }}>
                <div><label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Max GB</label><input type="number" className="form-control" step="0.01" min="0" placeholder="Unlimited" value={tier.max_gb ?? ''} onChange={e => updateDbTier(tier.id, 'max_gb', e.target.value || null)} /></div>
                <div><label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Price per GB ($)</label><input type="number" className="form-control" step="0.01" min="0" value={tier.price_per_gb} onChange={e => updateDbTier(tier.id, 'price_per_gb', parseFloat(e.target.value) || 0)} /></div>
                <button style={{ background: '#fee2e2', color: 'var(--red)', border: '1.5px solid rgba(220, 38, 38, 0.25)', padding: '6px 12px', fontSize: '0.8rem', borderRadius: 7, cursor: 'pointer', alignSelf: 'end', fontFamily: "'Inter', sans-serif", fontWeight: 600 }} onClick={() => removeDbTier(tier.id)}>Remove</button>
              </div>
            ))}
            <button className="btn btn-primary" style={{ marginTop: 8 }} onClick={addDbTier}>+ Add Tier</button>
          </div>
        </div>
      </div>

      {/* Runs Pricing */}
      <div style={sectionStyle}>
        <div style={headerStyle}><div style={{ width: 4, height: 20, background: 'var(--accent)', borderRadius: 4 }} /><h2 style={{ fontSize: '1rem', fontWeight: 700, margin: 0 }}>Number of Runs Pricing</h2></div>
        <div style={bodyStyle}>
          <div className="two-column">
            <div className="form-group"><label>Base Price ($)</label><input type="number" className="form-control" step="0.01" min="0" value={runsBasePrice} onChange={e => setRunsBasePrice(parseFloat(e.target.value) || 0)} /></div>
            <div className="form-group"><label>Price per Run ($)</label><input type="number" className="form-control" step="0.01" min="0" value={runsPricePerRun} onChange={e => setRunsPricePerRun(parseFloat(e.target.value) || 0)} /></div>
          </div>
          <div className="two-column">
            <div className="form-group"><label>Bulk Discount - Min Runs</label><input type="number" className="form-control" min="0" value={runsMinRuns} onChange={e => setRunsMinRuns(parseInt(e.target.value) || 0)} /></div>
            <div className="form-group"><label>Bulk Discount - Percent (%)</label><input type="number" className="form-control" step="0.1" min="0" max="100" value={runsDiscountPercent} onChange={e => setRunsDiscountPercent(parseFloat(e.target.value) || 0)} /></div>
          </div>
        </div>
      </div>

      {/* Deployment Pricing */}
      <div style={sectionStyle}>
        <div style={headerStyle}><div style={{ width: 4, height: 20, background: 'var(--accent)', borderRadius: 4 }} /><h2 style={{ fontSize: '1rem', fontWeight: 700, margin: 0 }}>Deployment Type Pricing</h2></div>
        <div style={bodyStyle}>
          <div className="two-column">
            <div className="form-group"><label>In-house VM ($)</label><input type="number" className="form-control" step="0.01" min="0" value={deployInhouse} onChange={e => setDeployInhouse(parseFloat(e.target.value) || 0)} /></div>
            <div className="form-group"><label>Client Premises ($)</label><input type="number" className="form-control" step="0.01" min="0" value={deployClient} onChange={e => setDeployClient(parseFloat(e.target.value) || 0)} /></div>
          </div>
        </div>
      </div>

      {/* WHERE Clauses */}
      <div style={sectionStyle}>
        <div style={headerStyle}><div style={{ width: 4, height: 20, background: 'var(--accent)', borderRadius: 4 }} /><h2 style={{ fontSize: '1rem', fontWeight: 700, margin: 0 }}>WHERE Clauses Pricing</h2></div>
        <div style={bodyStyle}>
          <div className="form-group"><label>Base Price ($)</label><input type="number" className="form-control" step="0.01" min="0" value={whereBasePrice} onChange={e => setWhereBasePrice(parseFloat(e.target.value) || 0)} /></div>
        </div>
      </div>

      {/* BIRT Complexity */}
      <div style={sectionStyle}>
        <div style={headerStyle}><div style={{ width: 4, height: 20, background: 'var(--accent)', borderRadius: 4 }} /><h2 style={{ fontSize: '1rem', fontWeight: 700, margin: 0 }}>BIRT Reports Complexity Pricing</h2></div>
        <div style={bodyStyle}>
          <div className="complexity-grid">
            {[0, 1, 2, 3, 4, 5].map(level => (
              <div key={level} style={{ padding: 14, background: 'var(--surface2)', borderRadius: 9, border: '1.5px solid var(--border)' }}>
                <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, display: 'block', marginBottom: 4 }}>Complexity {level}</label>
                <input type="number" className="form-control" step="0.01" min="0" placeholder="Price per report" value={birtComplexity[level]?.price_per_report || ''} onChange={e => updateBirtComp(level, 'price_per_report', e.target.value)} />
                <input type="text" className="form-control" style={{ marginTop: 5 }} placeholder="Description" value={birtComplexity[level]?.description || ''} onChange={e => updateBirtComp(level, 'description', e.target.value)} />
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Maximo */}
      <div style={sectionStyle}>
        <div style={headerStyle}><div style={{ width: 4, height: 20, background: 'var(--accent)', borderRadius: 4 }} /><h2 style={{ fontSize: '1rem', fontWeight: 700, margin: 0 }}>Maximo Upgrade Feature Pricing</h2></div>
        <div style={bodyStyle}>
          <div className="form-group"><label>Base Price ($)</label><input type="number" className="form-control" step="0.01" min="0" value={maximoBasePrice} onChange={e => setMaximoBasePrice(parseFloat(e.target.value) || 0)} /></div>
          <div className="form-group"><label>Price per Feature ($)</label><input type="number" className="form-control" step="0.01" min="0" value={maximoPricePerFeature} onChange={e => setMaximoPricePerFeature(parseFloat(e.target.value) || 0)} /></div>
        </div>
      </div>

      {/* Add-On Installation */}
      <div style={sectionStyle}>
        <div style={headerStyle}><div style={{ width: 4, height: 20, background: 'var(--accent)', borderRadius: 4 }} /><h2 style={{ fontSize: '1rem', fontWeight: 700, margin: 0 }}>Add-On Installation Pricing</h2></div>
        <div style={bodyStyle}>
          <div className="three-column">
            <div className="form-group"><label>Db2 Installation Price ($)</label><input type="number" className="form-control" step="0.01" min="0" value={addonDb2} onChange={e => setAddonDb2(parseFloat(e.target.value) || 0)} /></div>
            <div className="form-group"><label>Birt Installation Price ($)</label><input type="number" className="form-control" step="0.01" min="0" value={addonBirt} onChange={e => setAddonBirt(parseFloat(e.target.value) || 0)} /></div>
            <div className="form-group"><label>Maximo Installation Price ($)</label><input type="number" className="form-control" step="0.01" min="0" value={addonMaximo} onChange={e => setAddonMaximo(parseFloat(e.target.value) || 0)} /></div>
          </div>
        </div>
      </div>

      <button onClick={saveAllPricing} style={{ background: 'var(--green)', width: '100%', padding: 14, fontSize: '1rem', marginTop: 28, borderRadius: 'var(--radius-sm)', boxShadow: '0 4px 14px rgba(22, 163, 74, 0.25)', color: '#fff', border: 'none', fontFamily: "'Inter', sans-serif", fontWeight: 700, cursor: 'pointer', transition: 'background 0.18s' }}>
        💾 Save All Pricing Configuration
      </button>
    </div>
  );
}
