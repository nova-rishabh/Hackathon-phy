import { PageLoader } from "@/components/Loader";

// Shown by Next.js while a page loads: a thin bar along the top and the RollWatch eye, blinking.
export default function Loading() {
  return (
    <>
      <span className="pageload-bar" aria-hidden="true"><i /></span>
      <PageLoader label="loading" />
    </>
  );
}
