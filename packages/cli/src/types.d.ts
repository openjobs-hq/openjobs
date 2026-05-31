// Ambient module declarations for the few CLI deps that don't ship
// their own .d.ts files at the version pinned in package.json.

declare module "bs58" {
  /** Encode a Uint8Array as a base58 string. */
  export function encode(buffer: Uint8Array): string;
  /** Decode a base58 string into a Uint8Array. */
  export function decode(str: string): Uint8Array;
  const _default: { encode: typeof encode; decode: typeof decode };
  export default _default;
}
