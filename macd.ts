export interface MACDConfig {
  fastPeriod: number;
  slowPeriod: number;
  signalPeriod: number;
  stopLossPct: number;
  takeProfitPct: number;
}

export const defaultConfig: MACDConfig = {
  fastPeriod: 12,
  slowPeriod: 26,
  signalPeriod: 9,
  stopLossPct: 0.08,
  takeProfitPct: 0.20,
};

function calculateEMA(values: number[], period: number): number[] {
  const k = 2 / (period + 1);
  const ema: number[] = [values[0]];
  for (let i = 1; i < values.length; i++) {
    ema.push(values[i] * k + ema[i - 1] * (1 - k));
  }
  return ema;
}

export function calculateMACD(
  closes: number[],
  config: MACDConfig = defaultConfig
): { macd: number[]; signal: number[]; histogram: number[] } {
  const fastEMA = calculateEMA(closes, config.fastPeriod);
  const slowEMA = calculateEMA(closes, config.slowPeriod);
  const macd = fastEMA.map((f, i) => f - slowEMA[i]);
  const signal = calculateEMA(macd, config.signalPeriod);
  const histogram = macd.map((m, i) => m - signal[i]);
  return { macd, signal, histogram };
}

export function generateSignals(
  closes: number[],
  config: MACDConfig = defaultConfig
): Array<{ index: number; signal: 1 | -1 | 0; macd: number; signalLine: number }> {
  const { macd, signal } = calculateMACD(closes, config);

  return closes.map((_, i) => {
    if (i === 0) return { index: i, signal: 0 as const, macd: macd[i], signalLine: signal[i] };
    const bullishCross = macd[i - 1] < signal[i - 1] && macd[i] > signal[i];
    const bearishCross = macd[i - 1] > signal[i - 1] && macd[i] < signal[i];
    const s = bullishCross ? 1 : bearishCross ? -1 : 0;
    return { index: i, signal: s as 1 | -1 | 0, macd: macd[i], signalLine: signal[i] };
  });
}
