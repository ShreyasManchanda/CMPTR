import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  CartesianGrid,
} from 'recharts';
import './TrendChart.css';

function formatStoreLabel(store) {
  if (!store) return '—';
  return store
    .replace(/^www\./, '')
    .replace(/^shop-us\./, '')
    .split('.')[0]
    .slice(0, 10);
}

export default function TrendChart({ competitors, ourPrice, currency = '₹' }) {
  if (!competitors || competitors.length === 0) return null;

  const data = competitors
    .filter((c) => c.price != null)
    .map((c, i) => ({
      rank: i + 1,
      label: formatStoreLabel(c.store),
      fullName: c.store || 'Unknown',
      price: c.price,
    }))
    .sort((a, b) => a.price - b.price)
    .map((row, i) => ({ ...row, rank: i + 1 }));

  const barCount = data.length;
  const barSize = Math.min(40, Math.max(12, Math.floor(300 / barCount) - 6));
  const useAngledLabels = barCount > 5;
  const bottomMargin = useAngledLabels ? 52 : 24;

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const row = payload[0].payload;
      return (
        <div className="trend-tooltip">
          <p className="trend-tooltip__store">
            {row.fullName.replace('www.', '').replace('shop-us.', '')}
          </p>
          <p className="trend-tooltip__price">
            {currency} {Number(payload[0].value).toLocaleString()}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="trend-chart">
      {ourPrice != null && (
        <div className="trend-chart__your-price">
          Your price: {currency}{ourPrice.toLocaleString()}
        </div>
      )}
      <p className="trend-chart__hint">Hover a bar for the full store name</p>
      <ResponsiveContainer width="100%" height={240}>
        <BarChart
          data={data}
          margin={{ top: 28, right: 16, left: 4, bottom: bottomMargin }}
          barCategoryGap={barCount > 6 ? '18%' : '24%'}
          barSize={barSize}
        >
          <defs>
            <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#10B981" stopOpacity={1} />
              <stop offset="50%" stopColor="#0EA572" stopOpacity={0.85} />
              <stop offset="100%" stopColor="#065F46" stopOpacity={0.6} />
            </linearGradient>
          </defs>

          <CartesianGrid
            strokeDasharray="4 4"
            stroke="rgba(255,255,255,0.04)"
            vertical={false}
          />

          <XAxis
            dataKey="label"
            fontSize={10}
            tickLine={false}
            axisLine={false}
            interval={0}
            height={useAngledLabels ? 48 : 28}
            tick={{
              fill: '#A1A1AA',
              fontFamily: 'Geist Mono, monospace',
              dy: useAngledLabels ? 4 : 8,
            }}
            angle={useAngledLabels ? -38 : 0}
            textAnchor={useAngledLabels ? 'end' : 'middle'}
          />

          <YAxis
            fontSize={10}
            tickLine={false}
            axisLine={false}
            tickFormatter={(val) => `${currency}${val}`}
            tick={{
              fill: '#A1A1AA',
              fontFamily: 'Geist Mono, monospace',
              dx: -4,
            }}
            width={52}
            domain={[0, (dataMax) => Math.ceil(dataMax * 1.25)]}
          />

          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />

          <Bar
            dataKey="price"
            fill="url(#barGradient)"
            stroke="rgba(16,185,129,0.3)"
            strokeWidth={1}
            radius={[4, 4, 0, 0]}
          />

          {ourPrice != null && (
            <ReferenceLine
              y={ourPrice}
              stroke="#FAFAFA"
              strokeDasharray="6 3"
              strokeWidth={1}
              strokeOpacity={0.8}
            />
          )}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
