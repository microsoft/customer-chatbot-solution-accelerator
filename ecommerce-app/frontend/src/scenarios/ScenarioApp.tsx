import { useEffect } from 'react';
import { AppHeader } from '@/components/Layout/AppHeader';
import { hostAppTitle, hostComplianceBanner, resolveHostScenario } from '@/lib/hostConfig';
import { BankingApp } from '@/scenarios/banking/BankingApp';
import { EcommerceApp } from '@/scenarios/ecommerce/EcommerceApp';
import { HealthcareApp } from '@/scenarios/healthcare/HealthcareApp';

export function ScenarioApp() {
  const scenario = resolveHostScenario();
  const banner = hostComplianceBanner();

  useEffect(() => {
    document.title = hostAppTitle();
  }, [scenario]);

  return (
    <div className="h-screen bg-background overflow-hidden">
      <AppHeader />
      {banner ? (
        <div className="border-b bg-muted/40 px-6 py-2 text-xs text-muted-foreground text-center">
          {banner}
        </div>
      ) : null}
      <div className={`flex ${banner ? 'h-[calc(100vh-5.5rem)]' : 'h-[calc(100vh-4rem)]'}`}>
        <div className="flex-1 min-h-0">
          {scenario === 'healthcare' ? (
            <HealthcareApp />
          ) : scenario === 'banking' ? (
            <BankingApp />
          ) : (
            <EcommerceApp />
          )}
        </div>
      </div>
    </div>
  );
}
