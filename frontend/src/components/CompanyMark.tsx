interface CompanyMarkProps {
  symbol: string;
}

export function CompanyMark({ symbol }: CompanyMarkProps) {
  const key = symbol.toUpperCase();

  if (key === "MSFT") {
    return (
      <span aria-hidden="true" className="company-mark msft-mark">
        <span />
        <span />
        <span />
        <span />
      </span>
    );
  }

  if (key === "AAPL") {
    return <span aria-hidden="true" className="company-mark apple-mark" />;
  }

  if (key === "NVDA") {
    return (
      <span aria-hidden="true" className="company-mark nvda-mark">
        N
      </span>
    );
  }

  if (key === "AMD") {
    return (
      <span aria-hidden="true" className="company-mark amd-mark">
        <span />
      </span>
    );
  }

  if (key === "SPY") {
    return (
      <span aria-hidden="true" className="company-mark spy-mark">
        S
      </span>
    );
  }

  return (
    <span aria-hidden="true" className="company-mark default-mark">
      {key.slice(0, 1)}
    </span>
  );
}
