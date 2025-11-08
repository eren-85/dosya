/**
 * Market Type Selector Component
 * Toggle between Spot and Futures markets
 */

import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { MARKET_TYPES, MarketType } from '@/lib/constants';

interface MarketTypeSelectorProps {
  value: MarketType;
  onChange: (value: MarketType) => void;
  disabled?: boolean;
}

export function MarketTypeSelector({ value, onChange, disabled }: MarketTypeSelectorProps) {
  return (
    <Tabs value={value} onValueChange={(v) => onChange(v as MarketType)}>
      <TabsList>
        {MARKET_TYPES.map((type) => (
          <TabsTrigger
            key={type.value}
            value={type.value}
            disabled={disabled}
          >
            {type.label}
          </TabsTrigger>
        ))}
      </TabsList>
    </Tabs>
  );
}
