import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import './TrendChart.css';

export default function TrendChart({ competitors, ourPrice, currency = '₹' }) {
  if (!competitors || competitors.length === 0) return null;

  const data = competitors
    .filter(c => c.price != null)
    .map(c => ({
      name: c.store || 'Unknown',
      price: c.price,
    }))
    .sort((a, b) => a.price - b.price);

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="trend-tooltip">
          <p className="trend-tooltip__store">{payload[0].payload.name}</p>
          <p className="trend-tooltip__price">{currency} {Number(payload[0].value).toLocaleString()}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="trend-chart">
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} margin={{ top: 20, right: 16, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--accent)" stopOpacity={0.6} />
              <stop offset="100%" stopColor="var(--accent)" stopOpacity={0.1} />
            </linearGradient>
          </defs>
          <XAxis
            dataKey="name"
            stroke="var(--text-secondary)"
            fontSize={12}
            tickLine={false}
            axisLine={false}
            tick={{ fill: 'rgba(255,255,255,0.4)', dy: 8 }}
          />
          <YAxis
            stroke="var(--text-secondary)"
            fontSize={12}
            tickLine={false}
            axisLine={false}
            tickFormatter={(val) => `${currency}${val}`}
            tick={{ fill: 'rgba(255,255,255,0.4)', dx: -8 }}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.04)' }} />
          <Bar 
            dataKey="price" 
            fill="url(#barGradient)" 
            stroke="var(--accent)"
            strokeWidth={1}
            radius={[4, 4, 0, 0]} 
          />
          {ourPrice != null && (
            <ReferenceLine
              y={ourPrice}
              stroke="#fff"
              strokeDasharray="4 4"
              label={{
                position: 'top',
                value: `Your price: ${currency}${ourPrice.toLocaleString()}`,
                fill: '#fff',
                fontSize: 11,
              }}
            />
          )}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
