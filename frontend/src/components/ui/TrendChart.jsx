import { BarChart, Bar, XAxis, YAxis, Tooltip, 
  ResponsiveContainer, ReferenceLine, CartesianGrid } 
  from 'recharts';
import './TrendChart.css';

export default function TrendChart({ 
  competitors, ourPrice, currency = '₹' 
}) {
  if (!competitors || competitors.length === 0) return null;

  const data = competitors
    .filter(c => c.price != null)
    .map((c, i) => ({
      name: `Store ${i + 1}`,
      fullName: c.store || 'Unknown',
      price: c.price,
    }))
    .sort((a, b) => a.price - b.price);

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="trend-tooltip">
          <p className="trend-tooltip__store">
            {payload[0].payload.fullName
              .replace('www.','')
              .replace('shop-us.','')}
          </p>
          <p className="trend-tooltip__price">
            {currency} {Number(payload[0].value)
              .toLocaleString()}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="trend-chart">
      {ourPrice != null && (
        <div style={{
          position: 'absolute',
          top: '10px',
          right: '16px',
          background: 'rgba(10, 10, 10, 0.9)',
          border: '1px solid rgba(16, 185, 129, 0.3)',
          borderRadius: '6px',
          padding: '6px 12px',
          fontFamily: 'Geist Mono, monospace',
          fontSize: '14px',
          fontWeight: 600,
          color: '#FAFAFA',
          zIndex: 10,
        }}>
          Your price: {currency}{ourPrice.toLocaleString()}
        </div>
      )}
      <ResponsiveContainer width="100%" height={280}>
        <BarChart 
          data={data} 
          margin={{ top: 28, right: 48, left: 8, bottom: 8 }}
          barSize={40}
        >
          <defs>
            <linearGradient id="barGradient" 
              x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#10B981" 
                    stopOpacity={1} />
              <stop offset="50%" stopColor="#0EA572" 
                    stopOpacity={0.85} />
              <stop offset="100%" stopColor="#065F46" 
                    stopOpacity={0.6} />
            </linearGradient>
          </defs>

          <CartesianGrid
            strokeDasharray="4 4"
            stroke="rgba(255,255,255,0.04)"
            vertical={false}
          />

          <XAxis
            dataKey="name"
            fontSize={10}
            tickLine={false}
            axisLine={false}
            tick={{ 
              fill: '#A1A1AA',
              fontFamily: 'Geist Mono, monospace',
              dy: 8 
            }}
            interval={0}
          />

          <YAxis
            fontSize={10}
            tickLine={false}
            axisLine={false}
            tickFormatter={(val) => `${currency}${val}`}
            tick={{ 
              fill: '#A1A1AA',
              fontFamily: 'Geist Mono, monospace',
              dx: -4 
            }}
            width={52}
            domain={[0, dataMax => 
              Math.ceil(dataMax * 1.25)
            ]}
          />

          <Tooltip 
            content={<CustomTooltip />} 
            cursor={{ fill: 'rgba(255,255,255,0.03)' }} 
          />

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