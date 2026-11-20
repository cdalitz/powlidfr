#
# Two functions for computing indices for the match between
# a groundtruth segmentation G and a test segmentation S:
#
#  meanIoU(G,S)
#     mean of intersection over union between G segment
#     and the S segment with the largest overlap
#
#  segmentation_error(G,S)
#     matches overlaps between G and S sgements and counts
#     the number of missed, split, merged, and split & merged segments
#
# Authors:
#  Mamdieh Shamsadini Motlagh and Christoph Dalitz, 2026
#
# Reference:
#  C. Dalitz, O., S. Goebbels, M. Shamsadini Motlagh, G. Gerzabek:
#  "Power Line Detection in Point Clouds with Point-SAM and RANSAC."
#  accepted for The International Conference on Computer Vision Theory
#  and Applications (VISAPP) (2027)
#

import numpy

# how points are marked as not assigned to a label
def _is_unassigned(value):
    if value is None or value == -1 or value == "-1":
        return True
    if isinstance(value, (float, numpy.floating)) and numpy.isnan(value):
        return True
    return False

# return all prediction labels of one point
def get_pred_ids(pred):
    if _is_unassigned(pred):
        return []
    return str(pred).split(";")

#  meanIoU
#     mean of intersection over union between G segment
#     and the S segment with the largest overlap
#  Return value:
#     one float representing the mean(IoU)
#  Arguments:
#     G = list of ground truth labels
#     S = list of test segment labels
def meanIoU(G, S):
    G = numpy.asarray(G, dtype=object) # dtype=object because sometimes we have NaN, "3", etc.
    S = numpy.asarray(S, dtype=object)

    # each GT label must correspond to one prediction label
    if len(G) != len(S):
        raise ValueError("G and S must have the same length")

    # all GT labels
    all_gt_ids = numpy.unique([gt for gt in G if not _is_unassigned(gt)])

    # for each powerlines we will cacluate an iou
    ious = []
    for gid in all_gt_ids:
        pred_for_gt = []

        # all prediction IDs overlapping this GT
        for gt, pred in zip(G, S):
            if gt == gid:
                if not _is_unassigned(pred):
                    pred_for_gt.append(pred)

        # no prediction overlaps this GT
        if len(pred_for_gt) == 0:
            ious.append(0)
            continue

        # prediction with the largest overlap
        best_pid = min(set(pred_for_gt), key=lambda pid: (-pred_for_gt.count(pid), int(pid)))

        TP = 0
        FP = 0
        FN = 0
        # calculate for each ground truth line an IoU.
        for gt, pred in zip(G, S):
            if _is_unassigned(pred):
                pred_count = 0
            else:
                pred_count = (pred == best_pid)
            if gt == gid and pred_count > 0:
                TP += pred_count
            elif gt == gid and pred_count == 0:
                FN += 1
            elif gt != gid and pred_count > 0:
                FP += pred_count

        iou = (TP / (TP + FP + FN) if (TP + FP + FN) > 0 else 0)
        ious.append(iou)

    # if there is no gt label
    if len(ious) == 0:
        return 0.0

    return numpy.mean(ious)

#  segmentation_error
#     matches overlaps between G and S sgements and counts
#     the number of missed, split, merged, and split & merged segments
#  Return value:
#     four integers: the numbers of correct, miss, split, merge, splitmerge
#  Arguments:
#     G = list of ground truth labels
#     S = list of test segment labels
def segmentation_error(G, S):
    G = numpy.asarray(G, dtype=object)
    S = numpy.asarray(S, dtype=object)

    if len(G) != len(S):
        raise ValueError("G and S must have the same length")

    # all Ground Truth labels
    all_gt_ids = set(gt for gt in G if not _is_unassigned(gt))

    # connections between GT and prediction labels
    pairs = []

    for gt, pred in zip(G, S):

        # point is not part of a GT label (should not happen)
        if _is_unassigned(gt):
            continue

        if not _is_unassigned(pred):
            pairs.append((gt, pred))

    correct = 0
    miss = 0
    split = 0
    merge = 0
    splitmerge = 0

    # initially, no ground-truth label has been examined.
    remaining_gts = set(all_gt_ids)

    while remaining_gts:

        # choose a gt to start
        start_gt = next(iter(remaining_gts))
        group_gts = {start_gt}
        group_preds = set()


        while True:
            old_gts = set(group_gts)
            old_preds = set(group_preds)

            # predictions connected to these GTs
            for gt, pid in pairs:
                if gt in group_gts:
                    group_preds.add(pid)

            # GTs connected to these predictions
            for gt, pid in pairs:
                if pid in group_preds:
                    group_gts.add(gt)

            # if nothing new were found it means out groups are full now
            if group_gts == old_gts and group_preds == old_preds:
                break

        remaining_gts -= group_gts

        number_gt = len(group_gts)
        number_pred = len(group_preds)

        if number_gt == 1 and number_pred == 0:
            miss += 1

        elif number_gt == 1 and number_pred == 1:
            correct += 1

        elif number_gt == 1 and number_pred > 1:
            split += 1

        elif number_gt > 1 and number_pred == 1:
            merge += 1

        elif number_gt > 1 and number_pred > 1:
            splitmerge += 1

    return correct, miss, split, merge, splitmerge
