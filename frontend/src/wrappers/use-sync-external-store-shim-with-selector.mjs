// ESM wrapper to re-export named export from CommonJS shim
import * as cjs from 'use-sync-external-store/shim/with-selector.js?commonjs'

const useSyncExternalStoreWithSelector = cjs.useSyncExternalStoreWithSelector || (cjs.default && cjs.default.useSyncExternalStoreWithSelector)

export { useSyncExternalStoreWithSelector }
export default cjs
